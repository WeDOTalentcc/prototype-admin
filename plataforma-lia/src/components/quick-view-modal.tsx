"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  X, MapPin, Linkedin, Github, Mail, Phone, Star,
  Briefcase, GraduationCap, Calendar, DollarSign,
  Eye, MessageCircle, UserPlus, Download, Share2,
  TrendingUp, Award, Target, Clock
} from "lucide-react"

interface Candidate {
  id: string
  name: string
  email: string
  phone: string
  position: string
  location: string
  score: number
  status: 'active' | 'prospect' | 'interview' | 'hired'
  tags: string[]
  linkedin: string
  skills: string[]
  experience: number
  education: string
  workHistory?: Array<{
    company: string
    position: string
    period: string
    description: string
  }>
  salary?: {
    current: number
    expected: number
  }
  notes?: string
  liaAnalysis?: {
    score: number
    strengths: string[]
    concerns: string[]
    recommendation: string
  }
}

interface QuickViewModalProps {
  candidate: Candidate | null
  isOpen: boolean
  onClose: () => void
  onNavigateToFullProfile: (candidate: Candidate) => void
  onScheduleInterview: (candidate: Candidate) => void
  onContactCandidate: (candidate: Candidate) => void
}

export function QuickViewModal({
  candidate,
  isOpen,
  onClose,
  onNavigateToFullProfile,
  onScheduleInterview,
  onContactCandidate
}: QuickViewModalProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'experience' | 'analysis'>('overview')

  if (!isOpen || !candidate) return null

  const getScoreColor = (score: number) => {
    if (score >= 90) return "text-green-600 bg-green-100"
    if (score >= 80) return "text-gray-800 dark:text-gray-200 bg-gray-100"
    if (score >= 70) return "text-yellow-600 bg-yellow-100"
    return "text-red-600 bg-red-100"
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-700 border-green-200'
      case 'prospect': return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200'
      case 'interview': return 'bg-purple-100 text-purple-700 border-purple-200'
      case 'hired': return 'bg-emerald-100 text-emerald-700 border-emerald-200'
      default: return 'bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-100'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Ativo'
      case 'prospect': return 'Prospecção'
      case 'interview': return 'Em Entrevista'
      case 'hired': return 'Contratado'
      default: return 'Desconhecido'
    }
  }

  return (
    <div 
      className="fixed inset-0 bg-black/50 backdrop-blur-[1px] flex items-center justify-center z-50 p-4"
      style={{ fontFamily: '"Open Sans", sans-serif' }}
    >
      <div className="bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-700 w-full max-w-4xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16">
              <AvatarFallback className="bg-gray-100 text-gray-800 dark:text-gray-200 font-medium text-lg">
                {candidate.name.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-base-ui font-semibold text-gray-800 dark:text-gray-200">
                {candidate.name}
              </h2>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {candidate.position}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <Badge className={`text-micro px-2 py-1 ${getStatusColor(candidate.status)}`}>
                  {getStatusLabel(candidate.status)}
                </Badge>
                <div className={`px-2 py-1 rounded-full text-micro font-bold ${getScoreColor(candidate.liaAnalysis?.score || candidate.score)}`}>
                  {candidate.liaAnalysis?.score || candidate.score}% LIA
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs">
              <Share2 className="w-4 h-4 mr-2" />
              Compartilhar
            </Button>
            <Button variant="outline" size="sm" className="bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs">
              <Download className="w-4 h-4 mr-2" />
              CV
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0 text-gray-400 hover:text-gray-600 hover:bg-gray-50"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {[
              { id: 'overview', label: 'Visão Geral', icon: Eye },
              { id: 'experience', label: 'Experiência', icon: Briefcase },
              { id: 'analysis', label: 'Análise LIA', icon: TrendingUp }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`group inline-flex items-center py-4 px-1 border-b-2 font-medium text-xs ${
                  activeTab === tab.id
                    ? 'border-gray-800 text-gray-800 dark:text-gray-200 dark:border-gray-200'
                    : 'border-transparent text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 hover:border-gray-300'
                }`}
              >
                <tab.icon className={`w-4 h-4 mr-2 ${
                  activeTab === tab.id ? 'text-gray-800 dark:text-gray-200' : 'text-gray-500 group-hover:text-gray-600'
                }`} />
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[50vh]">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Contact & Social */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-3">Contato</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs">
                      <Mail className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-400">{candidate.email}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <Phone className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-400">{candidate.phone}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <MapPin className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-400">{candidate.location}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <Linkedin className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      <a href={candidate.linkedin} target="_blank" rel="noopener noreferrer"
                         className="text-gray-600 dark:text-gray-400 hover:text-wedo-cyan-dark transition-colors">
                        LinkedIn Profile
                      </a>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-3">Informações</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs">
                      <Briefcase className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-400">{candidate.experience} anos de experiência</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <GraduationCap className="w-4 h-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-400">{candidate.education}</span>
                    </div>
                    {candidate.salary && (
                      <div className="flex items-center gap-2 text-xs">
                        <DollarSign className="w-4 h-4 text-gray-500" />
                        <span className="text-gray-600 dark:text-gray-400">
                          Atual: R$ {candidate.salary.current.toLocaleString()} |
                          Pretensão: R$ {candidate.salary.expected.toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Skills */}
              <div>
                <h3 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-3">Competências</h3>
                <div className="flex flex-wrap gap-2">
                  {candidate.skills.map((skill, index) => (
                    <Badge key={index} variant="outline" className="text-micro border-gray-200 dark:border-gray-600 text-gray-600 dark:text-gray-400">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Tags */}
              {candidate.tags.length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-3">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {candidate.tags.map((tag, index) => (
                      <Badge key={index} className="text-micro bg-gray-100 text-gray-800 dark:text-gray-200 border-gray-200">
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'experience' && (
            <div className="space-y-6">
              {candidate.workHistory && candidate.workHistory.length > 0 ? (
                <div>
                  <h3 className="text-xs font-medium text-gray-800 dark:text-gray-200 mb-4">Histórico Profissional</h3>
                  <div className="space-y-4">
                    {candidate.workHistory.map((job, index) => (
                      <div key={index} className="border-l-2 border-gray-200 pl-4 pb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-medium text-gray-800 dark:text-gray-200 text-xs">{job.position}</h4>
                          <Badge variant="outline" className="text-micro border-gray-100">{job.period}</Badge>
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-400 font-medium mb-2">{job.company}</p>
                        <p className="text-xs text-gray-600 dark:text-gray-400">{job.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Briefcase className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400 text-xs">Histórico profissional não disponível</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'analysis' && (
            <div className="space-y-6">
              {candidate.liaAnalysis ? (
                <>
                  {/* Score */}
                  <div className="text-center">
                    <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full text-2xl font-bold ${getScoreColor(candidate.liaAnalysis.score)}`}>
                      {candidate.liaAnalysis.score}%
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">Score de Compatibilidade LIA</p>
                  </div>

                  {/* Analysis */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-xs font-medium text-green-700 mb-3 flex items-center gap-2">
                        <Award className="w-4 h-4" />
                        Pontos Fortes
                      </h3>
                      <ul className="space-y-2">
                        {candidate.liaAnalysis.strengths.map((strength, index) => (
                          <li key={index} className="text-xs text-gray-600 dark:text-gray-400 flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-green-500 rounded-full mt-2 flex-shrink-0" />
                            {strength}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h3 className="text-xs font-medium text-yellow-700 mb-3 flex items-center gap-2">
                        <Target className="w-4 h-4" />
                        Pontos de Atenção
                      </h3>
                      <ul className="space-y-2">
                        {candidate.liaAnalysis.concerns.map((concern, index) => (
                          <li key={index} className="text-xs text-gray-600 dark:text-gray-400 flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-yellow-500 rounded-full mt-2 flex-shrink-0" />
                            {concern}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Recommendation */}
                  <div className="bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-700 rounded-md p-4">
                    <h3 className="text-xs font-medium text-gray-600 dark:text-gray-400 mb-2 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      Recomendação da LIA
                    </h3>
                    <p className="text-xs text-gray-800 dark:text-gray-200">{candidate.liaAnalysis.recommendation}</p>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <TrendingUp className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 dark:text-gray-400 text-xs">Análise da LIA não disponível</p>
                  <Button variant="outline" size="sm" className="mt-4 bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs">
                    <Target className="w-4 h-4 mr-2" />
                    Solicitar Análise
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between p-5 border-t border-gray-200 bg-gray-50 dark:bg-gray-900 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs">
              <Star className="w-4 h-4 mr-2" />
              Favoritar
            </Button>
            <Button variant="outline" size="sm" className="bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs">
              <UserPlus className="w-4 h-4 mr-2" />
              Adicionar a Lista
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => onContactCandidate(candidate)}
              className="bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs"
            >
              <MessageCircle className="w-4 h-4 mr-2" />
              Contatar
            </Button>
            <Button
              variant="outline"
              onClick={() => onScheduleInterview(candidate)}
              className="bg-white border border-gray-300 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 text-xs"
            >
              <Calendar className="w-4 h-4 mr-2" />
              Agendar
            </Button>
            <Button
              onClick={() => onNavigateToFullProfile(candidate)}
              className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200 text-xs"
            >
              <Eye className="w-4 h-4 mr-2" />
              Perfil Completo
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
