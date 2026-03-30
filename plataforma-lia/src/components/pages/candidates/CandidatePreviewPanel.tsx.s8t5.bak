"use client"

import React, { useState } from "react"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Calendar, Mail, MessageSquare, Star, Briefcase, User, Phone, Linkedin, X } from "lucide-react"
import { LIAIcon } from "@/components/ui/lia-icon"
import { LIAFeedbackWidget } from "@/components/calibration"
import { textStyles, badgeStyles, formatScore, formatScorePercent } from "@/lib/design-tokens"
import type { Candidate } from "@/components/pages/candidates/types"

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
                <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50 mb-2">Informações Básicas</h4>
                <div className="space-y-2">
                  <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <span className={`${textStyles.bodySmall} dark:text-gray-500`}>Cargo:</span>
                    <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>{candidate.position}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <span className={`${textStyles.bodySmall} dark:text-gray-500`}>Localização:</span>
                    <span className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>{candidate.location}</span>
                  </div>
                  <div className="flex justify-between items-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <span className={`${textStyles.bodySmall} dark:text-gray-500`}>Status:</span>
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
                <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50 mb-2">Score LIA</h4>
                <div className="bg-gray-100 dark:bg-gray-800 p-3 rounded-md">
                  <div className="flex items-center justify-between mb-2">
                    <span className={`${textStyles.label} dark:text-gray-200`}>Compatibilidade</span>
                    <span className="text-base font-bold text-gray-900 dark:text-gray-50">{formatScorePercent(candidate.score)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-gray-900 dark:bg-gray-50 h-1.5 rounded-full"
                      style={{width: `${formatScore(candidate.score)}%`}}
                    ></div>
                  </div>
                  <div className={`${textStyles.description} mt-1 dark:text-gray-400`}>
                    Score baseado em habilidades, experiência e fit cultural
                  </div>
                  <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-700">
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
                <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50 mb-2">Experiência Profissional</h4>
                <div className="space-y-3">
                  <div className="border-l-4 border-wedo-green pl-3 py-2 bg-wedo-green/10 dark:bg-wedo-green/20 rounded-r-lg">
                    <div className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>
                      Senior Developer
                    </div>
                    <div className={`${textStyles.bodySmall} text-wedo-green dark:text-wedo-green`}>
                      Tech Corp • 2021 - Atual
                    </div>
                    <div className={`${textStyles.bodySmall} mt-1 dark:text-gray-400`}>
                      Desenvolvimento de aplicações web com React, Node.js e PostgreSQL
                    </div>
                  </div>
                  <div className="border-l-4 border-gray-300 pl-3 py-2 bg-gray-50 dark:bg-gray-800 rounded-r-lg">
                    <div className={`${textStyles.label} text-gray-950 dark:text-gray-50`}>
                      Full Stack Developer
                    </div>
                    <div className={`${textStyles.bodySmall} dark:text-gray-500`}>
                      Startup XYZ • 2019 - 2021
                    </div>
                    <div className={`${textStyles.bodySmall} mt-1 dark:text-gray-400`}>
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
                <h4 className="text-xs font-semibold text-gray-950 dark:text-gray-50 mb-2">Habilidades Técnicas</h4>
                <div className="space-y-3">
                  <div>
                    <h5 className={`${textStyles.label} dark:text-gray-200 mb-1`}>Frontend</h5>
                    <div className="flex flex-wrap gap-1">
                      {['React', 'TypeScript', 'Next.js', 'Tailwind CSS'].map((skill, index) => (
                        <Badge key={index} className="text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 border-0">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">Backend</h5>
                    <div className="flex flex-wrap gap-2">
                      {['Node.js', 'Python', 'PostgreSQL', 'MongoDB'].map((skill, index) => (
                        <Badge key={index} className="text-xs bg-status-success/15 text-status-success border-0">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h5 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-2">Soft Skills</h5>
                    <div className="flex flex-wrap gap-2">
                      {['Liderança', 'Comunicação', 'Trabalho em equipe', 'Resolução de problemas'].map((skill, index) => (
                        <Badge key={index} className="text-xs bg-wedo-purple/15 text-wedo-purple border-0">
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
                <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-3">Informações de Contato</h4>
                <div className="space-y-3">
                  <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <Mail className="w-4 h-4 text-gray-800" />
                    <div>
                      <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{candidate.email}</div>
                      <div className="text-xs text-gray-800">Email principal</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <Phone className="w-4 h-4 text-gray-800" />
                    <div>
                      <div className="text-sm font-medium text-gray-950 dark:text-gray-50">{candidate.phone}</div>
                      <div className="text-xs text-gray-800">Telefone/WhatsApp</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <Linkedin className="w-4 h-4 text-gray-700 dark:text-gray-300" />
                    <div>
                      <div className="text-sm font-medium text-gray-900 dark:text-gray-100">Ver perfil LinkedIn</div>
                      <div className="text-xs text-gray-800 dark:text-gray-200">Perfil profissional</div>
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-gray-950 dark:text-gray-50 mb-3">Histórico de Interações</h4>
                <div className="space-y-2">
                  <div className="text-xs text-gray-800 dark:text-gray-400 p-2 bg-gray-100 dark:bg-gray-800 rounded-md">
                    📧 Email enviado há 2 dias
                  </div>
                  <div className="text-xs text-gray-800 dark:text-gray-400 p-2 bg-status-success/10 dark:bg-status-success/20 rounded-md">
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
      <div className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 flex flex-col h-full">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-3">
              <Avatar className="w-10 h-10">
                <AvatarImage
                  src={candidate.avatar || `https://ui-avatars.com/api/?name=${encodeURIComponent(candidate.name)}&background=60BED1&color=fff&size=150`}
                  alt={candidate.name}
                />
                <AvatarFallback className="bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold">
                  {candidate.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <div>
                <h3 className="font-semibold text-gray-950 dark:text-gray-50">{candidate.name}</h3>
                <p className="text-sm text-gray-800 dark:text-gray-500">{candidate.position}</p>
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
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="font-semibold text-gray-950 dark:text-gray-50">{formatScorePercent(candidate.score)}</div>
              <div className="text-gray-800">Score LIA</div>
            </div>
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
              <div className="font-semibold text-gray-950 dark:text-gray-50 flex items-center justify-center gap-1">
                <Star className="w-3 h-3 text-status-warning" />
                4.8
              </div>
              <div className="text-gray-800">Avaliação</div>
            </div>
            <div className="text-center p-2 bg-gray-50 dark:bg-gray-800 rounded-md">
              <Badge className={`text-xs ${
                candidate.status === 'active' ? 'bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success' :
                candidate.status === 'prospect' ? 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300' :
                candidate.status === 'interview' ? 'bg-status-warning/15 dark:bg-status-warning/30 text-status-warning dark:text-status-warning' :
                'bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200'
              }`}>
                {candidate.status === 'active' ? 'Ativo' :
                 candidate.status === 'prospect' ? 'Prospect' :
                 candidate.status === 'interview' ? 'Entrevista' : 'Contratado'}
              </Badge>
            </div>
          </div>
        </div>

        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-0" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 py-2 px-3 text-xs font-medium text-center border-b-2 ${
                  activeTab === tab.id
                    ? 'border-gray-950 text-gray-950 dark:border-gray-50 dark:text-gray-50'
                    : 'border-transparent text-gray-800 hover:text-gray-950 hover:border-gray-300 dark:text-gray-400 dark:hover:text-gray-300'
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

        <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
          <Button
            className="w-full gap-2 bg-gray-900 hover:bg-gray-800"
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
