"use client"


import { CURRENCY_SYMBOL } from"@/lib/pricing"
import { useState } from"react"
import { useModalA11y } from"@/hooks/ui/use-modal-a11y"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Button } from"@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { CandidateAvatar } from"@/components/candidate-profile/CandidateAvatar"
import { CandidateSkillsList } from"@/components/candidate-profile/CandidateSkillsList"
import {
  X, MessageCircle, Calendar, Clock, User, Phone, Mail, MapPin,
  Star, TrendingUp, Eye, Share2, Download, FileText, Edit,
  BrainCircuit, Target, Building, Briefcase, GraduationCap,
  ChevronRight, ThumbsUp, ThumbsDown, Plus, Send, History,
  Video, Linkedin, Globe, AlertCircle, CheckCircle, ArrowRight
} from"lucide-react"

interface ModalCandidate {
  id?: string | number
  name?: string
  [key: string]: unknown
}

interface CandidateModalProps {
  candidate: ModalCandidate
  isOpen: boolean
  onClose: () => void
  onUpdateCandidate?: (candidate: ModalCandidate) => void
  onAddNote?: (candidateId: number, note: string) => void
}

// Mock data for candidate details
const mockCandidateDetails = {
  fullName:"Maria Santos Silva",
  email:"maria.santos@email.com",
  phone:"+55 11 99999-1234",
  location:"São Paulo, SP",
  linkedinUrl:"https://linkedin.com/in/mariasantos",
  portfolio:"https://mariasantos.design",
  currentCompany:"TechCorp",
  currentRole:"UX Designer",
  experience:"6 anos",
  education: [
    {
      degree:"Bacharelado em Design",
      institution:"ESPM",
      year:"2018",
      location:"São Paulo, SP"
    }
  ],
  skills: ["Figma","Sketch","Prototyping","User Research","Design System","Adobe Creative Suite"],
  languages: ["Português (Nativo)","Inglês (Avançado)","Espanhol (Intermediário)"],
  salary: {
    current: `${CURRENCY_SYMBOL} 7.500`,
    expected: `${CURRENCY_SYMBOL} 9.000 - ${CURRENCY_SYMBOL} 12.000`
  },
  availability:"Disponível em 30 dias",
  source:"LinkedIn",
  appliedDate:"2025-03-15",
  liaScore: 8.7,
  skillsMatch: 92,
  status:"Em triagem",
  tags: ["Destaque","Portfolio Excelente","Referenciada"],

  // Histórico de movimentações
  movementHistory: [
    {
      id: 1,
      from: null,
      to:"applied",
      toName:"Aplicaram",
      date:"2025-03-15T10:30:00",
      user:"Sistema",
      notes:"Candidatura recebida via LinkedIn"
    },
    {
      id: 2,
      from:"applied",
      fromName:"Aplicaram",
      to:"screening",
      toName:"Triagem",
      date:"2025-03-16T14:20:00",
      user:"Ana Silva",
      notes:"Aprovada na triagem inicial - perfil compatível"
    }
  ],

  // Notas e comentários
  notes: [
    {
      id: 1,
      author:"Ana Silva",
      date:"2025-03-16T14:25:00",
      content:"Candidata com portfolio excepcional, muita experiência em produtos digitais. Recomendo seguir para entrevista técnica.",
      type:"positive"
    },
    {
      id: 2,
      author:"João Costa",
      date:"2025-03-15T16:45:00",
      content:"Nota IA muito alta, compatibilidade perfeita para nossa necessidade. Verificar disponibilidade para início.",
      type:"neutral"
    }
  ],

  // Interações
  interactions: [
    {
      id: 1,
      type:"email",
      title:"Email de confirmação enviado",
      date:"2025-03-15T10:35:00",
      description:"Confirmação de recebimento da candidatura"
    },
    {
      id: 2,
      type:"view",
      title:"CV visualizado",
      date:"2025-03-16T09:15:00",
      description:"Visualizado por Ana Silva"
    },
    {
      id: 3,
      type:"call",
      title:"Ligação agendada",
      date:"2025-03-17T14:00:00",
      description:"Entrevista telefônica marcada para amanhã"
    }
  ]
}

export function CandidateModal({ candidate, isOpen, onClose, onUpdateCandidate, onAddNote }: CandidateModalProps) {
  const [activeTab, setActiveTab] = useState("overview")
  const [newNote, setNewNote] = useState("")
  const [noteType, setNoteType] = useState<"positive" |"neutral" |"negative">("neutral")
  const dialogRef = useModalA11y(isOpen, onClose)

  if (!isOpen || !candidate) return null

  const candidateData = { ...candidate, ...mockCandidateDetails }

  const handleAddNote = () => {
    if (!newNote.trim()) return

    const note = {
      id: Date.now(),
      author:"Ana Silva", // Current user
      date: new Date().toISOString(),
      content: newNote,
      type: noteType
    }

    onAddNote?.(candidate.id as number, newNote as any)
    candidateData.notes.unshift(note)
    setNewNote("")
  }

  const handleStatusChange = (newStatus: string) => {
    const movement = {
      id: Date.now(),
      from: candidateData.status,
      fromName: candidateData.status,
      to: newStatus,
      toName: newStatus,
      date: new Date().toISOString(),
      user:"Ana Silva",
      notes: `Movido para ${newStatus} via modal`
    }

    candidateData.movementHistory.unshift(movement)
    candidateData.status = newStatus
    onUpdateCandidate?.(candidateData)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getInteractionIcon = (type: string) => {
    switch (type) {
      case 'email': return <Mail className="w-4 h-4 text-lia-text-secondary" />
      case 'call': return <Phone className="w-4 h-4 text-status-success" />
      case 'view': return <Eye className="w-4 h-4 text-lia-text-primary" />
      case 'meeting': return <Video className="w-4 h-4 text-wedo-purple" />
      default: return <MessageCircle className="w-4 h-4 text-lia-text-primary" />
    }
  }

  const getNoteColor = (type: string) => {
    switch (type) {
      case 'positive': return 'border-l-green-500 bg-status-success/10 dark:bg-status-success/10'
      case 'negative': return 'border-l-red-500 bg-status-error/10 dark:bg-status-error/10'
      default: return 'border-l-blue-500 bg-wedo-cyan/10'
    }
  }

  return (
    <div className="fixed inset-0 bg-lia-overlay flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="candidate-modal-title" className="w-full max-w-6xl max-h-[90vh] bg-lia-bg-primary rounded-xl overflow-hidden" onClick={e => e.stopPropagation()}>

        {/* Header */}
        <div className="flex items-center justify-between p-6 bg-lia-bg-secondary">
          <div className="flex items-center gap-4">

            <CandidateAvatar
              name={candidateData.fullName}
              avatarUrl={candidate.avatar as string | undefined}
              size="lg"
              className="w-16 h-16"
            />

            <div>
              <h2 id="candidate-modal-title" className="text-2xl font-semibold text-lia-text-primary">
                {candidateData.fullName}
              </h2>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-lia-text-secondary">
                  {candidateData.currentRole} • {candidateData.experience}
                </span>
                <Chip variant="neutral" muted className={`${candidateData.status === 'Em triagem' ? '' : 'bg-lia-bg-tertiary text-lia-text-secondary'}`}>
                  {candidateData.status}
                </Chip>
              </div>

              <div className="flex items-center gap-4 mt-2">
                <div className="flex items-center gap-1">
                  <BrainCircuit className="w-4 h-4 text-lia-text-secondary" />
                  <span className="text-sm font-medium text-wedo-cyan-dark">IA: {candidateData.liaScore}/10</span>
                </div>
                <div className="flex items-center gap-1">
                  <Target className="w-4 h-4 text-status-success" />
                  <span className="text-sm font-medium text-status-success">Match: {candidateData.skillsMatch}%</span>
                </div>
                <div className="flex items-center gap-1">
                  <MapPin className="w-4 h-4 text-lia-text-primary" />
                  <span className="text-sm text-lia-text-secondary">{candidateData.location}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" className="gap-2">
              <Download className="w-4 h-4" />
              CV
            </Button>
            <Button variant="outline" size="sm" className="gap-2">
              <Share2 className="w-4 h-4" />
              Compartilhar
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="h-8 w-8 p-0"
              aria-label="Fechar detalhes do candidato"
              data-dismiss="true"
            >
              <X className="w-4 h-4" aria-hidden="true" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-lia-bg-primary">
          <div className="flex gap-8 px-6">
            {[
              { id: 'overview', label: 'Visão Geral', icon: User },
              { id: 'history', label: 'Histórico', icon: History },
              { id: 'notes', label: 'Notas', icon: MessageCircle },
              { id: 'interactions', label: 'Interações', icon: Clock }
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-4 rounded-lg transition-colors motion-reduce:transition-none ${
 activeTab === tab.id
                    ? 'border-lia-btn-primary-bg text-lia-text-primary'
                    : 'border-transparent text-lia-text-primary hover:text-lia-text-primary dark:hover:text-lia-text-inverse'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 max-h-96">

          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Informações Pessoais */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2 text-lia-text-primary">
                    <User className="w-5 h-5" />
                    Informações Pessoais
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-lia-text-primary">Email</label>
                      <div className="flex items-center gap-2 mt-1">
                        <Mail className="w-4 h-4 text-lia-text-primary" />
                        <span className="text-sm text-lia-text-primary">{candidateData.email}</span>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-lia-text-primary">Telefone</label>
                      <div className="flex items-center gap-2 mt-1">
                        <Phone className="w-4 h-4 text-lia-text-primary" />
                        <span className="text-sm text-lia-text-primary">{candidateData.phone}</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-lia-text-primary">LinkedIn</label>
                      <div className="flex items-center gap-2 mt-1">
                        <Linkedin className="w-4 h-4 text-lia-text-secondary" />
                        <a href={candidateData.linkedinUrl} className="text-sm text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse hover:underline">Ver perfil</a>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-lia-text-primary">Portfolio</label>
                      <div className="flex items-center gap-2 mt-1">
                        <Globe className="w-4 h-4 text-lia-text-primary" />
                        <a href={candidateData.portfolio} className="text-sm text-lia-text-secondary hover:text-lia-text-primary dark:hover:text-lia-text-inverse hover:underline">Ver portfolio</a>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-lia-text-primary">Empresa Atual</label>
                    <div className="flex items-center gap-2 mt-1">
                      <Building className="w-4 h-4 text-lia-text-primary" />
                      <span className="text-sm text-lia-text-primary">
                        {candidateData.currentRole} na {candidateData.currentCompany}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Skills e Competências */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2 text-lia-text-primary">
                    <Star className="w-5 h-5" />
                    Skills e Competências
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-lia-text-primary mb-2 block">Habilidades Técnicas</label>
                    <CandidateSkillsList skills={candidateData.skills} />
                  </div>

                  <div>
                    <label className="text-sm font-medium text-lia-text-primary mb-2 block">Idiomas</label>
                    <div className="space-y-1">
                      {candidateData.languages.map((language: string, index: number) => (
                        <div key={language} className="text-sm text-lia-text-primary">
                          {language}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-lia-text-primary mb-2 block">Tags</label>
                    <div className="flex flex-wrap gap-2">
                      {candidateData.tags.map((tag: string, index: number) => (
                        <Chip density="relaxed" key={tag} variant="success" >
                          {tag}
                        </Chip>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Educação */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2 text-lia-text-primary">
                    <GraduationCap className="w-5 h-5" />
                    Formação
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {candidateData.education.map((edu: { degree?: string; institution?: string; year?: string; location?: string }, index: number) => (
                    <div key={`edu-${index}`} className="space-y-2">
                      <div className="font-medium text-lia-text-primary">{edu.degree}</div>
                      <div className="text-sm text-lia-text-secondary">
                        {edu.institution} • {edu.year} • {edu.location}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Expectativas */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2 text-lia-text-primary">
                    <Target className="w-5 h-5" />
                    Expectativas
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-lia-text-primary">Salário Atual</label>
                    <div className="text-sm text-lia-text-primary mt-1">{candidateData.salary.current}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-lia-text-primary">Pretensão Salarial</label>
                    <div className="text-sm text-lia-text-primary mt-1">{candidateData.salary.expected}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-lia-text-primary">Disponibilidade</label>
                    <div className="text-sm text-lia-text-primary mt-1">{candidateData.availability}</div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-lia-text-primary">
                  Histórico de Movimentações
                </h3>
                <div className="flex gap-2">
                  <select
                    className="px-3 py-1 text-sm border border-lia-border-default rounded-xl bg-lia-bg-primary"
                    onChange={(e) => handleStatusChange(e.target.value)}
                    value=""
                  >
                    <option value="">Mover para...</option>
                    <option value="screening">Triagem</option>
                    <option value="interview">Entrevista</option>
                    <option value="final">Final</option>
                    <option value="approved">Aprovado</option>
                    <option value="rejected">Rejeitado</option>
                  </select>
                </div>
              </div>

              <div className="space-y-4">
                {candidateData.movementHistory.map((movement: { id: number; from?: string | null; to?: string; toName?: string; fromName?: string; date?: string; user?: string; notes?: string }, index: number) => (
                  <div key={movement.id} className="flex gap-4 p-4 bg-lia-bg-secondary rounded-xl">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 bg-lia-border-medium rounded-full"></div>
                      {index < candidateData.movementHistory.length - 1 && (
                        <div className="w-0.5 h-8 bg-lia-border-default mt-2"></div>
                      )}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {movement.from && (
                          <>
                            <span className="text-sm font-medium text-lia-text-primary">
                              {movement.fromName}
                            </span>
                            <ArrowRight className="w-4 h-4 text-lia-text-primary" />
                          </>
                        )}
                        <span className="text-sm font-medium text-lia-text-primary">
                          {movement.toName}
                        </span>
                      </div>


                      <div className="text-xs text-lia-text-secondary mb-1">
                        {formatDate(movement.date!)} • por {movement.user}
                      </div>

                      {movement.notes && (

                        <div className="text-sm text-lia-text-primary">
                          {movement.notes}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notes Tab */}
          {activeTab === 'notes' && (
            <div className="space-y-6">

              {/* Add New Note */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg text-lia-text-primary">Adicionar Nova Nota</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setNoteType('positive')}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors motion-reduce:transition-none ${
 noteType === 'positive'
                          ? 'bg-status-success/15 dark:bg-status-success/20 text-status-success border-status-success/30 dark:border-status-success/30'
                          : 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default'
                      }`}
                    >
                      <ThumbsUp className="w-3 h-3 inline mr-1" />
                      Positiva
                    </button>
                    <button
                      onClick={() => setNoteType('neutral')}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors motion-reduce:transition-none ${
 noteType === 'neutral'
                          ? 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default'
                          : 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default'
                      }`}
                    >
                      <MessageCircle className="w-3 h-3 inline mr-1" />
                      Neutral
                    </button>
                    <button
                      onClick={() => setNoteType('negative')}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors motion-reduce:transition-none ${
 noteType === 'negative'
                          ? 'bg-status-error/15 dark:bg-status-error/20 text-status-error dark:text-status-error border-status-error/30 dark:border-status-error/30'
                          : 'bg-lia-bg-tertiary text-lia-text-secondary border-lia-border-default'
                      }`}
                    >
                      <ThumbsDown className="w-3 h-3 inline mr-1" />
                      Negativa
                    </button>
                  </div>

                  <textarea
                    value={newNote}
                    onChange={(e) => setNewNote(e.target.value)}
                    placeholder="Escreva sua nota ou comentário sobre o candidato..."
                    className="w-full p-3 border border-lia-border-default rounded-xl bg-lia-bg-primary text-lia-text-primary text-sm resize-none h-24 focus:outline-none focus:ring-2 focus:ring-lia-border-default/30"
                  />

                  <Button onClick={handleAddNote} className="gap-2" disabled={!newNote.trim()}>
                    <Send className="w-4 h-4" />
                    Adicionar Nota
                  </Button>
                </CardContent>
              </Card>

              {/* Existing Notes */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-lia-text-primary">
                  Notas e Comentários ({candidateData.notes.length})
                </h3>


                {candidateData.notes.map((note: { id: number; author: string; date?: string; content?: string; type?: string }) => (

                  <div key={note.id} className={`p-4 rounded-md border-l-4 ${getNoteColor(note.type ?? '')}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <CandidateAvatar name={note.author} size="sm" className="w-6 h-6" />
                        <span className="font-medium text-sm text-lia-text-primary">
                          {note.author}
                        </span>
                      </div>

                      <span className="text-xs text-lia-text-primary">
                        {formatDate(note.date!)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-primary leading-relaxed">
                      {note.content}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Interactions Tab */}
          {activeTab === 'interactions' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-lia-text-primary">
                Histórico de Interações
              </h3>

              <div className="space-y-3">
                {candidateData.interactions.map((interaction: { id: number; type?: string; title?: string; date?: string; description?: string }) => (
                  <div key={interaction.id} className="flex gap-4 p-4 bg-lia-bg-secondary rounded-xl">

                    <div className="mt-1">
                      {getInteractionIcon(interaction.type ||"")}
                    </div>

                    <div className="flex-1">
                      <div className="font-medium text-sm text-lia-text-primary mb-1">
                        {interaction.title}
                      </div>
                      <div className="text-sm text-lia-text-secondary mb-1">
                        {interaction.description}
                      </div>

                      <div className="text-xs text-lia-text-primary">
                        {formatDate(interaction.date!)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Quick Actions */}
              <Card className="mt-6">
                <CardHeader>
                  <CardTitle className="text-lg">Ações Rápidas</CardTitle>
                </CardHeader>
                <CardContent className="flex flex-wrap gap-2">
                  <Button variant="outline" size="sm" className="gap-2">
                    <Phone className="w-4 h-4" />
                    Ligar
                  </Button>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Mail className="w-4 h-4" />
                    Enviar Email
                  </Button>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Video className="w-4 h-4" />
                    Videochamada
                  </Button>
                  <Button variant="outline" size="sm" className="gap-2">
                    <Calendar className="w-4 h-4" />
                    Agendar Entrevista
                  </Button>
                  <Button variant="outline" size="sm" className="gap-2">
                    <MessageCircle className="w-4 h-4" />
                    WhatsApp
                  </Button>
                </CardContent>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
