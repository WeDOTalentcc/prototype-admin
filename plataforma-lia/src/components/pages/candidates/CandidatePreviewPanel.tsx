"use client"

import React, { useState } from"react"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Badge } from"@/components/ui/badge"
import { Button } from"@/components/ui/button"
import { Calendar, Mail, MessageSquare, Star, Briefcase, User, Phone, Linkedin, X } from"lucide-react"
import { LIAIcon } from"@/components/ui/lia-icon"
import { LIAFeedbackWidget } from"@/components/calibration"
import { textStyles, badgeStyles, formatScore, formatScorePercent } from"@/lib/design-tokens"
import type { Candidate } from"@/components/pages/candidates/types"

export function CandidatePreviewPanel({ candidate, onClose }: { candidate: Candidate; onClose: () => void }) {

    const [activeTab, setActiveTab] = useState('overview')

    const tabs = [
      { id: 'overview', label: 'Visão Geral', icon: User },
      { id: 'experience', label: 'Experiência', icon: Briefcase },
      { id: 'skills', label: 'Habilidades', icon: Star },
      { id: 'contact', label: 'Contato', icon: MessageSquare }
    ]

    const renderTabContent = () => {
      switch (activeTab) {
        case 'overview':
          return (
            <div className="space-y-6">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-primary mb-2">Informações Básicas</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <span className={`${textStyles.bodySmall}`}>Cargo:</span>
                    <span className={`${textStyles.label} text-lia-text-primary`}>{candidate.position}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <span className={`${textStyles.bodySmall}`}>Localização:</span>
                    <span className={`${textStyles.label} text-lia-text-primary`}>{candidate.location}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <span className={`${textStyles.bodySmall}`}>Status:</span>
                    <Badge className={`${
                      candidate.status === 'active' ? badgeStyles.success :
                      candidate.status === 'prospect' ? badgeStyles.info :
                      candidate.status === 'interview' ? badgeStyles.warning :
                      badgeStyles.default
                    } px-2 py-0.5`}>
                      {candidate.status === 'active' ? 'Ativo' :
                       candidate.status === 'prospect' ? 'Prospect' :
                       candidate.status === 'interview' ? 'Entrevista' : 'Contratado'}
                    </Badge>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-semibold text-lia-text-primary mb-2">Score LIA</h4>
                <div className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary p-3 rounded-xl">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`${textStyles.label}`}>Compatibilidade</span>
                    <span className="text-base font-bold text-lia-text-primary">{formatScorePercent(candidate.score)}</span>
                  </div>
                  <div className="w-full bg-lia-interactive-active rounded-full h-1.5">
                    <div
                      className="bg-lia-btn-primary-bg dark:bg-lia-bg-secondary h-1.5 rounded-full"
                      style={{width: `${formatScore(candidate.score)}%`}}
                    ></div>
                  </div>
                  <div className={`${textStyles.description} mt-1`}>
                    Score baseado em habilidades, experiência e aderência cultural
                  </div>
                  <div className="mt-3 pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <LIAFeedbackWidget
                      candidateId={candidate.id}
                      liaScore={candidate.score}
                      liaRecommendation={candidate.liaAnalysis?.recommendation}
                      compact={false}
                      showLabel={true}
                    />
                  </div>
                </div>
              </div>
            </div>
          )

        case 'experience':
          return (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-primary mb-2">Experiência Profissional</h4>
                <div className="space-y-3">
                  <div className="border-l-4 border-wedo-green pl-3 py-2 bg-wedo-green/10 dark:bg-wedo-green/20 rounded-r-lg">
                    <div className={`${textStyles.label} text-lia-text-primary`}>
                      Senior Developer
                    </div>
                    <div className={`${textStyles.bodySmall} text-wedo-green dark:text-wedo-green`}>
                      Tech Corp • 2021 - Atual
                    </div>
                    <div className={`${textStyles.bodySmall} mt-1`}>
                      Desenvolvimento de aplicações web com React, Node.js e PostgreSQL
                    </div>
                  </div>
                  <div className="border-l-4 border-lia-border-default pl-3 py-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-r-lg">
                    <div className={`${textStyles.label} text-lia-text-primary`}>
                      Full Stack Developer
                    </div>
                    <div className={`${textStyles.bodySmall}`}>
                      Startup XYZ • 2019 - 2021
                    </div>
                    <div className={`${textStyles.bodySmall} mt-1`}>
                      Desenvolvimento fullstack e arquitetura de sistemas
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )

        case 'skills':
          return (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-semibold text-lia-text-primary mb-2">Habilidades Técnicas</h4>
                <div className="space-y-3">
                  <div>
                    <h5 className={`${textStyles.label} mb-1`}>Frontend</h5>
                    <div className="flex flex-wrap gap-1">
                      {['React', 'TypeScript', 'Next.js', 'Tailwind CSS'].map((skill, index) => (
                        <Badge key={skill} className="text-xs bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary border-0">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-lia-text-primary mb-2">Backend</h5>
                    <div className="flex flex-wrap gap-2">
                      {['Node.js', 'Python', 'PostgreSQL', 'MongoDB'].map((skill, index) => (
                        <Badge key={skill} className="text-xs  border-0">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-lia-text-primary mb-2">Soft Skills</h5>
                    <div className="flex flex-wrap gap-2">
                      {['Liderança', 'Comunicação', 'Trabalho em equipe', 'Resolução de problemas'].map((skill, index) => (
                        <Badge key={skill} className="text-xs  border-0">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )

        case 'contact':
          return (
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-lia-text-primary mb-3">Informações de Contato</h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <Mail className="w-4 h-4 text-lia-text-primary" />
                    <div>
                      <div className="text-sm font-medium text-lia-text-primary">{candidate.email}</div>
                      <div className="text-xs text-lia-text-primary">Email principal</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <Phone className="w-4 h-4 text-lia-text-primary" />
                    <div>
                      <div className="text-sm font-medium text-lia-text-primary">{candidate.phone}</div>
                      <div className="text-xs text-lia-text-primary">Telefone/WhatsApp</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                    <Linkedin className="w-4 h-4 text-lia-text-secondary" />
                    <div>
                      <div className="text-sm font-medium text-lia-text-primary">Ver perfil LinkedIn</div>
                      <div className="text-xs text-lia-text-primary">Perfil profissional</div>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-lia-text-primary mb-3">Histórico de Interações</h4>
                <div className="space-y-2">
                  <div className="text-xs text-lia-text-primary p-2 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl">
                    📧 Email enviado há 2 dias
                  </div>
                  <div className="text-xs text-lia-text-primary p-2 bg-status-success/10 dark:bg-status-success/20 rounded-md">
                    📞 Ligação agendada para amanhã às 14h
                  </div>
                </div>
              </div>
            </div>
          )

        default:
          return null
      }
    }

    return (
      <div className="w-96 bg-lia-bg-primary dark:bg-lia-bg-secondary border-l border-lia-border-subtle dark:border-lia-border-subtle flex flex-col h-full">
        <div className="p-4 dark:border-lia-border-subtle">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage
                  src={candidate.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(candidate.name)}&background=60BED1&color=fff&size=150`}
                  alt={candidate.name}
                />
                <AvatarFallback className="bg-lia-bg-tertiary dark:bg-lia-bg-elevated text-lia-text-secondary font-semibold">
                  {candidate.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold text-lia-text-primary">{candidate.name}</h3>
                <p className="text-sm text-lia-text-primary">{candidate.position}</p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          <div className="grid grid-cols-3 gap-2 text-xs">
            <div className="text-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <div className="font-semibold text-lia-text-primary">{formatScorePercent(candidate.score)}</div>
              <div className="text-lia-text-primary">Score LIA</div>
            </div>
            <div className="text-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <div className="font-semibold text-lia-text-primary flex items-center justify-center gap-1">
                <Star className="w-3 h-3 text-status-warning" />
                4.8
              </div>
              <div className="text-lia-text-primary">Avaliação</div>
            </div>
            <div className="text-center p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
              <Badge className={`text-xs ${
                candidate.status === 'active' ? 'bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success' :
                candidate.status === 'prospect' ? 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary text-lia-text-secondary' :
                candidate.status === 'interview' ? 'bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning' :
                'bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-primary'
              }`}>
                {candidate.status === 'active' ? 'Ativo' :
                 candidate.status === 'prospect' ? 'Prospect' :
                 candidate.status === 'interview' ? 'Entrevista' : 'Contratado'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="dark:border-lia-border-subtle">
          <nav className="flex space-x-0" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-2 px-3 text-xs font-medium text-center rounded-lg ${
                  activeTab === tab.id
                    ? 'border-lia-btn-primary-bg text-lia-text-primary dark:border-lia-border-medium'
                    : 'border-transparent text-lia-text-primary hover:text-lia-text-primary hover:border-lia-border-default'
                }`}
              >
                <tab.icon className="w-3 h-3 mx-auto mb-1" />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {renderTabContent()}
        </div>

        <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle space-y-2">
          <Button
            className="w-full gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
            onClick={() => {}}
          >
            <Calendar className="w-4 h-4" />
            Agendar Entrevista
          </Button>
          <div className="grid grid-cols-2 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => {}}
            >
              <Mail className="w-4 h-4" />
              Email
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => {}}
            >
              <LIAIcon size="sm" />
              LIA
            </Button>
          </div>
        </div>
      </div>
    )
}
