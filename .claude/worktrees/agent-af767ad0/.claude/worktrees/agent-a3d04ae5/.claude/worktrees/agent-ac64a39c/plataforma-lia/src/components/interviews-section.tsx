"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Play, Calendar, Clock, User, Mail, Phone, FileText, Star, CheckCircle, AlertCircle, XCircle, MessageSquare } from "lucide-react"

const candidates = [
  {
    id: 1,
    name: "João Silva",
    position: "Frontend Developer",
    job: "Desenvolvedor React Sênior",
    date: "12 Mar 2025",
    time: "14:30",
    status: "Aprovado",
    score: 8.5,
    phone: "+55 11 99999-1234",
    email: "joao.silva@email.com",
    avatar: "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=150&h=150&fit=crop&crop=face"
  },
  {
    id: 2,
    name: "Maria Santos",
    position: "UX Designer",
    job: "Designer de Produto",
    date: "10 Mar 2025",
    time: "16:00",
    status: "Em análise",
    score: 7.8,
    phone: "+55 11 98888-5678",
    email: "maria.santos@email.com",
    avatar: "https://images.unsplash.com/photo-1494790108755-2616b612b95c?w=150&h=150&fit=crop&crop=face"
  },
  {
    id: 3,
    name: "Carlos Oliveira",
    position: "Backend Developer",
    job: "Desenvolvedor Node.js",
    date: "8 Mar 2025",
    time: "10:15",
    status: "Rejeitado",
    score: 6.2,
    phone: "+55 11 97777-9012",
    email: "carlos.oliveira@email.com",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face"
  }
]

const getStatusIcon = (status: string) => {
  switch (status) {
    case "Aprovado":
      return <CheckCircle className="w-4 h-4 text-green-600" />
    case "Em análise":
      return <AlertCircle className="w-4 h-4 text-orange-600" />
    case "Rejeitado":
      return <XCircle className="w-4 h-4 text-red-600" />
    default:
      return <Clock className="w-4 h-4 text-gray-600" />
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case "Aprovado":
      return "bg-green-50 text-green-700 border-green-200"
    case "Em análise":
      return "bg-orange-50 text-orange-700 border-orange-200"
    case "Rejeitado":
      return "bg-red-50 text-red-700 border-red-200"
    default:
      return "bg-gray-50 text-gray-800 dark:text-gray-200 border-gray-200"
  }
}

export function InterviewsSection() {
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-sans font-semibold text-gray-950 dark:text-gray-50">Últimas Triagens</h2>
        <Button variant="ghost" size="sm" className="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200">
          Ver mais
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {candidates.map((candidate) => (
          <div key={candidate.id} className="wedo-card p-5 hover:border-gray-300 dark:hover:border-gray-600 transition-all cursor-pointer">
            <div className="space-y-4">
              {/* Header com avatar, nome e status */}
              <div className="flex items-start gap-3">
                <Avatar className="w-12 h-12 flex-shrink-0">
                  <AvatarImage
                    src={candidate.avatar}
                    alt={candidate.name}
                    className="object-cover"
                  />
                  <AvatarFallback className="bg-gray-100 text-gray-600">
                    {candidate.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between mb-1">
                    <h3 className="font-semibold text-gray-950 dark:text-gray-50 text-sm leading-tight">
                      {candidate.name}
                    </h3>
                    {getStatusIcon(candidate.status)}
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{candidate.position}</p>

                  <Badge
                    variant="outline"
                    className={`text-xs px-2 py-1 ${getStatusBadge(candidate.status)}`}
                  >
                    {candidate.status}
                  </Badge>
                </div>
              </div>

              {/* Informações da vaga */}
              <div className="space-y-2">
                <div className="text-xs text-gray-600 dark:text-gray-400">
                  <span className="font-medium text-gray-800 dark:text-gray-200">Vaga:</span> {candidate.job}
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
                  <Calendar className="w-3 h-3 text-gray-600" />
                  <span>{candidate.date} às {candidate.time}</span>
                </div>
              </div>

              {/* Score */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Star className="w-4 h-4 text-yellow-500 fill-current" />
                  <span className="text-sm font-semibold text-gray-950 dark:text-gray-50">
                    {candidate.score}
                  </span>
                  <span className="text-xs text-gray-600">/10</span>
                </div>

                <div className="flex items-center gap-1">
                  <div className="w-16 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        candidate.score >= 8 ? 'bg-green-500' :
                        candidate.score >= 7 ? 'bg-yellow-500' :
                        candidate.score >= 6 ? 'bg-orange-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${(candidate.score / 10) * 100}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Contatos com botões intuitivos */}
              <div className="space-y-2 py-2 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-2">
                  <Phone className="w-3 h-3 text-gray-600" />
                  <span className="text-xs text-gray-600 dark:text-gray-400 flex-1">{candidate.phone}</span>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-6 px-2 text-xs bg-gray-50 hover:bg-gray-100 border-gray-200 text-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 dark:border-gray-600 dark:text-gray-200"
                    onClick={() => window.open(`https://wa.me/${candidate.phone.replace(/\D/g, '')}`, '_blank')}
                  >
                    WhatsApp
                  </Button>
                </div>
                <div className="flex items-center gap-2">
                  <Mail className="w-3 h-3 text-gray-600" />
                  <span className="text-xs text-gray-600 dark:text-gray-400 flex-1 truncate">{candidate.email}</span>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-6 px-2 text-xs bg-gray-50 hover:bg-gray-100 border-gray-200 text-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 dark:border-gray-600 dark:text-gray-200"
                    onClick={() => window.open(`mailto:${candidate.email}`, '_blank')}
                  >
                    Email
                  </Button>
                </div>
              </div>

              {/* Ações */}
              <div className="flex items-center gap-2 pt-2">
                <Button size="sm" variant="outline" className="flex-1 gap-1 text-xs h-8 bg-gray-50 hover:bg-gray-100 border-gray-200 hover:border-gray-300 text-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 dark:border-gray-600 dark:text-gray-200">
                  <MessageSquare className="w-3 h-3" />
                  Ver Chat
                </Button>
                <Button size="sm" variant="outline" className="flex-1 gap-1 text-xs h-8 bg-gray-50 hover:bg-gray-100 border-gray-200 hover:border-gray-300 text-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 dark:border-gray-600 dark:text-gray-200">
                  <FileText className="w-3 h-3" />
                  Perfil
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
