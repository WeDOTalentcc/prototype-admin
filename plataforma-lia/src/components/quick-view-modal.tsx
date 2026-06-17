"use client"


import { formatBRL } from"@/lib/pricing"
import { useState } from"react"
import { useModalA11y } from"@/hooks/ui/use-modal-a11y"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback } from"@/components/ui/avatar"
import {
  X, MapPin, Linkedin, Github, Mail, Phone, Star,
  Briefcase, GraduationCap, Calendar, DollarSign,
  Eye, MessageCircle, UserPlus, Download, Share2,
  TrendingUp, Award, Target, Clock
} from"lucide-react"

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
  const dialogRef = useModalA11y(isOpen, onClose)

  if (!isOpen || !candidate) return null

  const getScoreColor = (score: number) => {
    if (score >= 90) return"text-status-success bg-status-success/15"
    if (score >= 80) return"text-lia-text-primary bg-lia-bg-tertiary"
    if (score >= 70) return"text-status-warning bg-status-warning/15"
    return"text-status-error bg-status-error/15"
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return ' border-status-success/30'
      case 'prospect': return 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle'
      case 'interview': return ' border-wedo-purple/30'
      case 'hired': return ' border-status-success/30'
      default: return 'bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle'
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
      className="fixed inset-0 bg-lia-overlay backdrop-blur-[1px] flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-label={`Visualização rápida: ${candidate.name}`} className="bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle w-full max-w-4xl max-h-[90vh] overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between p-5">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16">
              <AvatarFallback className="bg-lia-bg-tertiary text-lia-text-primary font-medium text-lg">
                {candidate.name.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            <div>
              <h2 className="text-base-ui font-semibold text-lia-text-primary">
                {candidate.name}
              </h2>
              <p className="text-xs text-lia-text-tertiary">
                {candidate.position}
              </p>
              <div className="flex items-center gap-2 mt-1">
                <Chip variant="neutral" muted className={`text-micro px-2 py-1 ${getStatusColor(candidate.status)}`}>
                  {getStatusLabel(candidate.status)}
                </Chip>
                <div className={`px-2 py-1 rounded-full text-micro font-bold ${getScoreColor(candidate.liaAnalysis?.score || candidate.score)}`}>
                  {candidate.liaAnalysis?.score || candidate.score}% IA
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse text-lia-text-primary text-xs">
              <Share2 className="w-4 h-4 mr-2" />
              Compartilhar
            </Button>
            <Button variant="outline" size="sm" className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse text-lia-text-primary text-xs">
              <Download className="w-4 h-4 mr-2" />
              CV
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0 text-lia-text-secondary hover:text-lia-text-secondary hover:bg-lia-bg-secondary"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="px-6 pt-2 pb-3">
          <nav className="flex gap-1 p-1 bg-lia-bg-tertiary rounded-lg w-fit" aria-label="Tabs">
            {[
              { id: 'overview', label: 'Visão Geral', icon: Eye },
              { id: 'experience', label: 'Experiência', icon: Briefcase },
              { id: 'analysis', label: 'Análise de IA', icon: TrendingUp }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as Parameters<typeof setActiveTab>[0])}
                className={`group inline-flex items-center py-2 px-3 rounded-md font-medium text-xs transition-all ${
 activeTab === tab.id
                    ? 'bg-lia-bg-primary shadow-sm text-lia-text-primary'
                    : 'text-lia-text-secondary hover:text-lia-text-primary'
                }`}
              >
                <tab.icon className={`w-4 h-4 mr-2 ${
 activeTab === tab.id ? 'text-lia-text-primary' : 'text-lia-text-secondary group-hover:text-lia-text-primary'
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
                  <h3 className="text-xs font-medium text-lia-text-primary mb-3">Contato</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs">
                      <Mail className="w-4 h-4 text-lia-text-secondary" />
                      <span className="text-lia-text-secondary">{candidate.email}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <Phone className="w-4 h-4 text-lia-text-secondary" />
                      <span className="text-lia-text-secondary">{candidate.phone}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <MapPin className="w-4 h-4 text-lia-text-secondary" />
                      <span className="text-lia-text-secondary">{candidate.location}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <Linkedin className="w-4 h-4 text-lia-text-secondary" />
                      <a href={candidate.linkedin} target="_blank" rel="noopener noreferrer"
                         className="text-lia-text-secondary hover:text-lia-text-primary transition-colors motion-reduce:transition-none">
                        LinkedIn Profile
                      </a>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="text-xs font-medium text-lia-text-primary mb-3">Informações</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs">
                      <Briefcase className="w-4 h-4 text-lia-text-secondary" />
                      <span className="text-lia-text-secondary">{candidate.experience} anos de experiência</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs">
                      <GraduationCap className="w-4 h-4 text-lia-text-secondary" />
                      <span className="text-lia-text-secondary">{candidate.education}</span>
                    </div>
                    {candidate.salary && (
                      <div className="flex items-center gap-2 text-xs">
                        <DollarSign className="w-4 h-4 text-lia-text-secondary" />
                        <span className="text-lia-text-secondary">
                          Atual: {formatBRL(candidate.salary.current)} |
                          Pretensão: {formatBRL(candidate.salary.expected)}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Skills */}
              <div>
                <h3 className="text-xs font-medium text-lia-text-primary mb-3">Competências</h3>
                <div className="flex flex-wrap gap-2">
                  {candidate.skills.map((skill) => (
                    <Chip key={skill} variant="neutral" className="text-micro border-lia-border-subtle dark:border-lia-border-default text-lia-text-secondary">
                      {skill}
                    </Chip>
                  ))}
                </div>
              </div>

              {/* Tags */}
              {candidate.tags.length > 0 && (
                <div>
                  <h3 className="text-xs font-medium text-lia-text-primary mb-3">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {candidate.tags.map((tag) => (
                      <Chip variant="neutral" muted key={tag} className="text-micro bg-lia-bg-tertiary text-lia-text-primary border-lia-border-subtle">
                        {tag}
                      </Chip>
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
                  <h3 className="text-xs font-medium text-lia-text-primary mb-4">Histórico Profissional</h3>
                  <div className="space-y-4">
                    {candidate.workHistory.map((job, index) => (
                      <div key={`job-${index}-${job.company || (job as any).title}`} className="border-l-2 border-lia-border-subtle pl-4 pb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <h4 className="font-medium text-lia-text-primary text-xs">{job.position}</h4>
                          <Chip variant="neutral" className="text-micro border-lia-border-subtle">{job.period}</Chip>
                        </div>
                        <p className="text-xs text-lia-text-secondary font-medium mb-2">{job.company}</p>
                        <p className="text-xs text-lia-text-secondary">{job.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-8">
                  <Briefcase className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
                  <p className="text-lia-text-secondary text-xs">Histórico profissional não disponível</p>
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
                    <div className={`inline-flex items-center justify-center w-20 h-20 rounded-full text-2xl font-semibold ${getScoreColor(candidate.liaAnalysis.score)}`}>
                      {candidate.liaAnalysis.score}%
                    </div>
                    <p className="text-xs text-lia-text-tertiary mt-2">Score de Compatibilidade LIA</p>
                  </div>

                  {/* Analysis */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-xs font-medium text-status-success mb-3 flex items-center gap-2">
                        <Award className="w-4 h-4" />
                        Pontos Fortes
                      </h3>
                      <ul className="space-y-2">
                        {candidate.liaAnalysis.strengths.map((strength, index) => (
                          <li key={`str-${index}`} className="text-xs text-lia-text-secondary flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-status-success rounded-full mt-2 flex-shrink-0" />
                            {strength}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h3 className="text-xs font-medium text-status-warning mb-3 flex items-center gap-2">
                        <Target className="w-4 h-4" />
                        Pontos de Atenção
                      </h3>
                      <ul className="space-y-2">
                        {candidate.liaAnalysis.concerns.map((concern, index) => (
                          <li key={`con-${index}`} className="text-xs text-lia-text-secondary flex items-start gap-2">
                            <div className="w-1.5 h-1.5 bg-status-warning rounded-full mt-2 flex-shrink-0" />
                            {concern}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {/* Recommendation */}
                  <div className="bg-lia-bg-secondary dark:bg-lia-bg-elevated border border-lia-border-subtle dark:border-lia-border-subtle rounded-xl p-4">
                    <h3 className="text-xs font-medium text-lia-text-secondary mb-2 flex items-center gap-2">
                      <TrendingUp className="w-4 h-4" />
                      Recomendação de IA
                    </h3>
                    <p className="text-xs text-lia-text-primary">{candidate.liaAnalysis.recommendation}</p>
                  </div>
                </>
              ) : (
                <div className="text-center py-8">
                  <TrendingUp className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
                  <p className="text-lia-text-secondary text-xs">Análise da LIA não disponível</p>
                  <Button variant="outline" size="sm" className="mt-4 bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse text-lia-text-primary text-xs">
                    <Target className="w-4 h-4 mr-2" />
                    Solicitar Análise
                  </Button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between p-5 bg-lia-bg-secondary dark:bg-lia-bg-primary rounded-b-xl">
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse text-lia-text-primary text-xs">
              <Star className="w-4 h-4 mr-2" />
              Favoritar
            </Button>
            <Button variant="outline" size="sm" className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse text-lia-text-primary text-xs">
              <UserPlus className="w-4 h-4 mr-2" />
              Adicionar a Lista
            </Button>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => onContactCandidate(candidate)}
              className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse text-lia-text-primary text-xs"
            >
              <MessageCircle className="w-4 h-4 mr-2" />
              Contatar
            </Button>
            <Button
              variant="outline"
              onClick={() => onScheduleInterview(candidate)}
              className="bg-lia-bg-primary border border-lia-border-default hover:bg-lia-bg-secondary dark:bg-lia-bg-secondary dark:border-lia-border-default dark:hover:bg-lia-bg-inverse text-lia-text-primary text-xs"
            >
              <Calendar className="w-4 h-4 mr-2" />
              Agendar
            </Button>
            <Button
              onClick={() => onNavigateToFullProfile(candidate)}
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active text-xs"
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
