"use client"

import { useState } from "react"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  X, MessageCircle, Calendar, Clock, User, Phone, Mail, MapPin,
  Star, TrendingUp, Eye, Share2, Download, FileText, Edit,
  BrainCircuit, Target, Building, Briefcase, GraduationCap,
  ChevronRight, ThumbsUp, ThumbsDown, Plus, Send, History,
  Video, Linkedin, Globe, AlertCircle, CheckCircle, ArrowRight
} from "lucide-react"

interface CandidateModalProps {
  candidate: any
  isOpen: boolean
  onClose: () => void
  onUpdateCandidate?: (candidate: any) => void
  onAddNote?: (candidateId: number, note: string) => void
}

// Mock data for candidate details
const mockCandidateDetails = {
  fullName: "Maria Santos Silva",
  email: "maria.santos@email.com",
  phone: "+55 11 99999-1234",
  location: "São Paulo, SP",
  linkedinUrl: "https://linkedin.com/in/mariasantos",
  portfolio: "https://mariasantos.design",
  currentCompany: "TechCorp",
  currentRole: "UX Designer",
  experience: "6 anos",
  education: [
    {
      degree: "Bacharelado em Design",
      institution: "ESPM",
      year: "2018",
      location: "São Paulo, SP"
    }
  ],
  skills: ["Figma", "Sketch", "Prototyping", "User Research", "Design System", "Adobe Creative Suite"],
  languages: ["Português (Nativo)", "Inglês (Avançado)", "Espanhol (Intermediário)"],
  salary: {
    current: "R$ 7.500",
    expected: "R$ 9.000 - R$ 12.000"
  },
  availability: "Disponível em 30 dias",
  source: "LinkedIn",
  appliedDate: "2025-03-15",
  liaScore: 8.7,
  skillsMatch: 92,
  status: "Em triagem",
  tags: ["Destaque", "Portfolio Excelente", "Referenciada"],

  // Histórico de movimentações
  movementHistory: [
    {
      id: 1,
      from: null,
      to: "applied",
      toName: "Aplicaram",
      date: "2025-03-15T10:30:00",
      user: "Sistema",
      notes: "Candidatura recebida via LinkedIn"
    },
    {
      id: 2,
      from: "applied",
      fromName: "Aplicaram",
      to: "screening",
      toName: "Triagem",
      date: "2025-03-16T14:20:00",
      user: "Ana Silva",
      notes: "Aprovada na triagem inicial - perfil compatível"
    }
  ],

  // Notas e comentários
  notes: [
    {
      id: 1,
      author: "Ana Silva",
      date: "2025-03-16T14:25:00",
      content: "Candidata com portfolio excepcional, muita experiência em produtos digitais. Recomendo seguir para entrevista técnica.",
      type: "positive"
    },
    {
      id: 2,
      author: "João Costa",
      date: "2025-03-15T16:45:00",
      content: "Score LIA muito alto, skills matching perfeito para nossa necessidade. Verificar disponibilidade para início.",
      type: "neutral"
    }
  ],

  // Interações
  interactions: [
    {
      id: 1,
      type: "email",
      title: "Email de confirmação enviado",
      date: "2025-03-15T10:35:00",
      description: "Confirmação de recebimento da candidatura"
    },
    {
      id: 2,
      type: "view",
      title: "CV visualizado",
      date: "2025-03-16T09:15:00",
      description: "Visualizado por Ana Silva"
    },
    {
      id: 3,
      type: "call",
      title: "Ligação agendada",
      date: "2025-03-17T14:00:00",
      description: "Entrevista telefônica marcada para amanhã"
    }
  ]
}

export function CandidateModal({ candidate, isOpen, onClose, onUpdateCandidate, onAddNote }: CandidateModalProps) {
  const [activeTab, setActiveTab] = useState("overview")
  const [newNote, setNewNote] = useState("")
  const [noteType, setNoteType] = useState<"positive" | "neutral" | "negative">("neutral")

  if (!isOpen || !candidate) return null

  const candidateData = { ...candidate, ...mockCandidateDetails }

  const handleAddNote = () => {
    if (!newNote.trim()) return

    const note = {
      id: Date.now(),
      author: "Ana Silva", // Current user
      date: new Date().toISOString(),
      content: newNote,
      type: noteType
    }

    onAddNote?.(candidate.id, newNote)
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
      user: "Ana Silva",
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
      case 'email': return <Mail className="w-4 h-4 text-gray-600 dark:text-gray-400" />
      case 'call': return <Phone className="w-4 h-4 text-status-success" />
      case 'view': return <Eye className="w-4 h-4 text-gray-800 dark:text-gray-200" />
      case 'meeting': return <Video className="w-4 h-4 text-wedo-purple" />
      default: return <MessageCircle className="w-4 h-4 text-gray-800 dark:text-gray-200" />
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
    <div className="fixed inset-0 bg-black/50 dark:bg-gray-950/70 flex items-center justify-center z-50 p-4">
      <div className="w-full max-w-6xl max-h-[90vh] bg-white dark:bg-gray-800 rounded-md overflow-hidden">

        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700">
          <div className="flex items-center gap-4">
            <Avatar className="w-16 h-16">
              <AvatarImage src={candidate.avatar} alt={candidateData.fullName} />
              <AvatarFallback className="text-lg">
                {candidateData.fullName.split(' ').map((n: string) => n[0]).join('')}
              </AvatarFallback>
            </Avatar>

            <div>
              <h2 className="text-2xl font-semibold text-gray-950 dark:text-gray-50">
                {candidateData.fullName}
              </h2>
              <div className="flex items-center gap-3 mt-1">
                <span className="text-gray-600 dark:text-gray-400">
                  {candidateData.currentRole} • {candidateData.experience}
                </span>
                <Badge className={`${candidateData.status === 'Em triagem' ? 'bg-status-warning/15 text-status-warning dark:text-status-warning' : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}>
                  {candidateData.status}
                </Badge>
              </div>

              <div className="flex items-center gap-4 mt-2">
                <div className="flex items-center gap-1">
                  <BrainCircuit className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                  <span className="text-sm font-medium text-wedo-cyan-dark">LIA: {candidateData.liaScore}/10</span>
                </div>
                <div className="flex items-center gap-1">
                  <Target className="w-4 h-4 text-status-success" />
                  <span className="text-sm font-medium text-status-success">Match: {candidateData.skillsMatch}%</span>
                </div>
                <div className="flex items-center gap-1">
                  <MapPin className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                  <span className="text-sm text-gray-600 dark:text-gray-400">{candidateData.location}</span>
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
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
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
                className={`flex items-center gap-2 py-4 border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'border-gray-900 text-gray-900 dark:border-gray-100 dark:text-gray-100'
                    : 'border-transparent text-gray-800 dark:text-gray-200 hover:text-gray-950 dark:hover:text-gray-50'
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
                  <CardTitle className="text-lg flex items-center gap-2 text-gray-950 dark:text-gray-50">
                    <User className="w-5 h-5" />
                    Informações Pessoais
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Email</label>
                      <div className="flex items-center gap-2 mt-1">
                        <Mail className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                        <span className="text-sm text-gray-950 dark:text-gray-50">{candidateData.email}</span>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Telefone</label>
                      <div className="flex items-center gap-2 mt-1">
                        <Phone className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                        <span className="text-sm text-gray-950 dark:text-gray-50">{candidateData.phone}</span>
                      </div>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">LinkedIn</label>
                      <div className="flex items-center gap-2 mt-1">
                        <Linkedin className="w-4 h-4 text-gray-600" />
                        <a href={candidateData.linkedinUrl} className="text-sm text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100 hover:underline">Ver perfil</a>
                      </div>
                    </div>
                    <div>
                      <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Portfolio</label>
                      <div className="flex items-center gap-2 mt-1">
                        <Globe className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                        <a href={candidateData.portfolio} className="text-sm text-gray-700 hover:text-gray-900 dark:text-gray-300 dark:hover:text-gray-100 hover:underline">Ver portfolio</a>
                      </div>
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Empresa Atual</label>
                    <div className="flex items-center gap-2 mt-1">
                      <Building className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                      <span className="text-sm text-gray-950 dark:text-gray-50">
                        {candidateData.currentRole} na {candidateData.currentCompany}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Skills e Competências */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2 text-gray-950 dark:text-gray-50">
                    <Star className="w-5 h-5" />
                    Skills e Competências
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">Habilidades Técnicas</label>
                    <div className="flex flex-wrap gap-2">
                      {candidateData.skills.map((skill: string, index: number) => (
                        <Badge key={index} variant="secondary" className="text-xs">
                          {skill}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">Idiomas</label>
                    <div className="space-y-1">
                      {candidateData.languages.map((language: string, index: number) => (
                        <div key={index} className="text-sm text-gray-950 dark:text-gray-50">
                          {language}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="text-sm font-medium text-gray-800 dark:text-gray-200 mb-2 block">Tags</label>
                    <div className="flex flex-wrap gap-2">
                      {candidateData.tags.map((tag: string, index: number) => (
                        <Badge key={index} variant="outline" className="text-xs border-status-success/30 text-status-success">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Educação */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2 text-gray-950 dark:text-gray-50">
                    <GraduationCap className="w-5 h-5" />
                    Formação
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {candidateData.education.map((edu: any, index: number) => (
                    <div key={index} className="space-y-2">
                      <div className="font-medium text-gray-950 dark:text-gray-50">{edu.degree}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">
                        {edu.institution} • {edu.year} • {edu.location}
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>

              {/* Expectativas */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2 text-gray-950 dark:text-gray-50">
                    <Target className="w-5 h-5" />
                    Expectativas
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Salário Atual</label>
                    <div className="text-sm text-gray-950 dark:text-gray-50 mt-1">{candidateData.salary.current}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Pretensão Salarial</label>
                    <div className="text-sm text-gray-950 dark:text-gray-50 mt-1">{candidateData.salary.expected}</div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-800 dark:text-gray-200">Disponibilidade</label>
                    <div className="text-sm text-gray-950 dark:text-gray-50 mt-1">{candidateData.availability}</div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                  Histórico de Movimentações
                </h3>
                <div className="flex gap-2">
                  <select
                    className="px-3 py-1 text-sm border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700"
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
                {candidateData.movementHistory.map((movement: any, index: number) => (
                  <div key={movement.id} className="flex gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-md">
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 bg-gray-400 dark:bg-gray-800 rounded-full"></div>
                      {index < candidateData.movementHistory.length - 1 && (
                        <div className="w-0.5 h-8 bg-gray-300 dark:bg-gray-600 mt-2"></div>
                      )}
                    </div>

                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {movement.from && (
                          <>
                            <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                              {movement.fromName}
                            </span>
                            <ArrowRight className="w-4 h-4 text-gray-800 dark:text-gray-200" />
                          </>
                        )}
                        <span className="text-sm font-medium text-gray-950 dark:text-gray-50">
                          {movement.toName}
                        </span>
                      </div>

                      <div className="text-xs text-gray-600 dark:text-gray-400 mb-1">
                        {formatDate(movement.date)} • por {movement.user}
                      </div>

                      {movement.notes && (
                        <div className="text-sm text-gray-800 dark:text-gray-200">
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
                  <CardTitle className="text-lg text-gray-950 dark:text-gray-50">Adicionar Nova Nota</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setNoteType('positive')}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                        noteType === 'positive'
                          ? 'bg-status-success/15 dark:bg-status-success/20 text-status-success dark:text-status-success border-status-success/30 dark:border-status-success/30'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600'
                      }`}
                    >
                      <ThumbsUp className="w-3 h-3 inline mr-1" />
                      Positiva
                    </button>
                    <button
                      onClick={() => setNoteType('neutral')}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                        noteType === 'neutral'
                          ? 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 border-gray-300 dark:border-gray-600'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600'
                      }`}
                    >
                      <MessageCircle className="w-3 h-3 inline mr-1" />
                      Neutral
                    </button>
                    <button
                      onClick={() => setNoteType('negative')}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                        noteType === 'negative'
                          ? 'bg-status-error/15 dark:bg-status-error/20 text-status-error dark:text-status-error border-status-error/30 dark:border-status-error/30'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 border-gray-300 dark:border-gray-600'
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
                    className="w-full p-3 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-700 text-gray-950 dark:text-gray-50 text-sm resize-none h-24 focus:outline-none focus:ring-2 focus:ring-gray-400/30"
                  />

                  <Button onClick={handleAddNote} className="gap-2" disabled={!newNote.trim()}>
                    <Send className="w-4 h-4" />
                    Adicionar Nota
                  </Button>
                </CardContent>
              </Card>

              {/* Existing Notes */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                  Notas e Comentários ({candidateData.notes.length})
                </h3>

                {candidateData.notes.map((note: any) => (
                  <div key={note.id} className={`p-4 rounded-md border-l-4 ${getNoteColor(note.type)}`}>
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Avatar className="w-6 h-6">
                          <AvatarFallback className="text-xs">
                            {note.author.split(' ').map((n: string) => n[0]).join('')}
                          </AvatarFallback>
                        </Avatar>
                        <span className="font-medium text-sm text-gray-950 dark:text-gray-50">
                          {note.author}
                        </span>
                      </div>
                      <span className="text-xs text-gray-800 dark:text-gray-200">
                        {formatDate(note.date)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-800 dark:text-gray-200 leading-relaxed">
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
              <h3 className="text-lg font-semibold text-gray-950 dark:text-gray-50">
                Histórico de Interações
              </h3>

              <div className="space-y-3">
                {candidateData.interactions.map((interaction: any) => (
                  <div key={interaction.id} className="flex gap-4 p-4 bg-gray-50 dark:bg-gray-700 rounded-md">
                    <div className="mt-1">
                      {getInteractionIcon(interaction.type)}
                    </div>

                    <div className="flex-1">
                      <div className="font-medium text-sm text-gray-950 dark:text-gray-50 mb-1">
                        {interaction.title}
                      </div>
                      <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                        {interaction.description}
                      </div>
                      <div className="text-xs text-gray-800 dark:text-gray-200">
                        {formatDate(interaction.date)}
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
