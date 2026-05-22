"use client"

import { formatBRL } from"@/lib/pricing"
import { useState } from"react"
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  CheckCircle, Clock, FileText, Mail, Phone,
  Eye, Calendar, MessageSquare, X
} from"lucide-react"
import { type ApprovedCandidate, kanbanStages } from"./onboarding-premium-types"

interface CandidateOnboardingModalProps {
  candidate: ApprovedCandidate
  onClose: () => void
}

export function CandidateOnboardingModal({ candidate, onClose }: CandidateOnboardingModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'communications' | 'schedule'>('overview')

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
      <div className="bg-lia-bg-primary rounded-xl w-full max-w-5xl h-[90vh] flex flex-col">
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16">
              <AvatarImage src={candidate.avatar} alt={candidate.name} />
              <AvatarFallback>{candidate.name.split(' ').map(n => n[0]).join('')}</AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-xl font-semibold text-lia-text-primary">{candidate.name}</h2>
              <p className="text-lia-text-secondary">{candidate.position} • {candidate.department}</p>
              <div className="flex items-center gap-2 mt-1">
                <Chip variant="neutral" muted className={kanbanStages.find(s => s.id === candidate.stage)?.color}>
                  {kanbanStages.find(s => s.id === candidate.stage)?.name}
                </Chip>
                <Chip variant="neutral">
                  {candidate.progress}% concluído
                </Chip>
              </div>
            </div>
          </div>
          <Button variant="ghost" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="flex border-b px-6">
          {[
            { id: 'overview', label: 'Visão Geral', icon: Eye },
            { id: 'documents', label: 'Documentos', icon: FileText },
            { id: 'communications', label: 'Comunicações', icon: MessageSquare },
            { id: 'schedule', label: 'Agenda', icon: Calendar }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as Parameters<typeof setActiveTab>[0])}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium transition-colors motion-reduce:transition-none ${
                activeTab === tab.id
                  ?"text-lia-text-secondary rounded-lg bg-lia-bg-tertiary dark:border-lia-border-medium"
                  :"text-lia-text-secondary hover:text-lia-text-primary"
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Informações do Colaborador</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-lia-text-secondary">Email</p>
                        <p className="text-sm">{candidate.email}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-lia-text-secondary">Telefone</p>
                        <p className="text-sm">{candidate.phone}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-lia-text-secondary">Gestor</p>
                        <p className="text-sm">{candidate.manager}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-lia-text-secondary">Salário</p>
                        <p className="text-sm">{formatBRL(candidate.salary)}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-lia-text-secondary">Data de Contratação</p>
                        <p className="text-sm">{new Date(candidate.hireDate).toLocaleDateString('pt-BR')}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-lia-text-secondary">Início</p>
                        <p className="text-sm">{new Date(candidate.startDate).toLocaleDateString('pt-BR')}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Progresso do Onboarding</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-lia-text-secondary">Progresso Geral</span>
                        <span className="text-sm font-medium">{candidate.progress}%</span>
                      </div>
                      <div className="w-full bg-lia-interactive-active rounded-full h-3">
                        <div
                          className="bg-lia-bg-inverse dark:bg-lia-text-tertiary h-3 rounded-full"
                          style={{width: `${candidate.progress}%`}}
                        />
                      </div>
                      <div className="space-y-2">
                        {kanbanStages.map(stage => (
                          <div key={stage.id} className="flex items-center justify-between">
                            <span className="text-sm text-lia-text-secondary">{stage.name}</span>
                            <CheckCircle
                              className={`w-4 h-4 ${
                                kanbanStages.findIndex(s => s.id === candidate.stage) >= kanbanStages.findIndex(s => s.id === stage.id)
                                  ? 'text-status-success'
                                  : 'text-lia-text-secondary'
                              }`}
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Ações Rápidas</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <Button className="w-full gap-2">
                      <MessageSquare className="w-4 h-4" />
                      Enviar WhatsApp
                    </Button>
                    <Button variant="outline" className="w-full gap-2">
                      <Mail className="w-4 h-4" />
                      Enviar Email
                    </Button>
                    <Button variant="outline" className="w-full gap-2">
                      <Calendar className="w-4 h-4" />
                      Agendar Exame
                    </Button>
                    <Button variant="outline" className="w-full gap-2">
                      <Phone className="w-4 h-4" />
                      Ligar
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-base">Próximas Tarefas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex items-center gap-3 p-2 bg-status-warning/10 rounded-md">
                        <Clock className="w-4 h-4 text-status-warning" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">Solicitar comprovante de residência</p>
                          <p className="text-xs text-lia-text-secondary">Vence hoje</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 p-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
                        <Calendar className="w-4 h-4 text-lia-text-secondary" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">Agendar exame admissional</p>
                          <p className="text-xs text-lia-text-secondary">Vence em 2 dias</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          )}

          {activeTab === 'documents' && (
            <div className="space-y-4">
              <h3 className="text-xs font-medium">Documentos</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {candidate.documents.map(doc => (
                  <Card key={doc.id}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <h4 className="font-medium">{doc.name}</h4>
                        <Chip
                          variant={doc.status === 'rejected' ? 'danger' : doc.status === 'approved' ? 'success' : 'neutral'}
                          muted={doc.status === 'uploaded'}
                        >
                          {doc.status === 'approved' ? 'Aprovado' :
                           doc.status === 'uploaded' ? 'Enviado' :
                           doc.status === 'rejected' ? 'Rejeitado' : 'Pendente'}
                        </Chip>
                      </div>
                      <p className="text-sm text-lia-text-secondary mb-3">{doc.type}</p>
                      {doc.isRequired && (
                        <Chip density="relaxed" variant="neutral" >Obrigatório</Chip>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'communications' && (
            <div className="space-y-4">
              <h3 className="text-xs font-medium">Histórico de Comunicações</h3>
              <div className="text-center py-8 text-lia-text-primary">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50 text-lia-text-secondary" />
                <p className="text-sm">Nenhuma comunicação enviada ainda</p>
              </div>
            </div>
          )}

          {activeTab === 'schedule' && (
            <div className="space-y-4">
              <h3 className="text-xs font-medium">Agenda de Onboarding</h3>
              <div className="text-center py-8 text-lia-text-primary">
                <Calendar className="w-8 h-8 mx-auto mb-2 opacity-50 text-lia-text-secondary" />
                <p className="text-sm">Agenda será configurada automaticamente</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
