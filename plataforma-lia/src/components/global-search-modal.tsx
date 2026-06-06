"use client"

import { useState, useEffect, useRef } from"react"
import { useRouter } from "next/navigation"
import { useLocale } from "next-intl"
import { navigationCatalog } from "@/lib/navigation/navigation-commands"
import { useCommandCatalog } from "@/hooks/lia/use-command-catalog"
import { Button } from"@/components/ui/button"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import {
  Search, X, Filter, User, Briefcase, MessageSquare, BarChart3,
  FileText, Clock, Star, ChevronRight, Zap, Calendar, MapPin,
  Mail, Phone, BookOpen, Settings, ArrowRight, Brain, Compass, Sparkles
} from"lucide-react"

interface SearchResult {
  id: string
  type:"candidate" |"job" |"conversation" |"document" |"automation" |"setting"
  title: string
  subtitle: string
  description: string
  metadata?: {
    status?: string
    date?: string
    location?: string
    score?: number
    priority?:"high" |"medium" |"low"
  }
  actions?: Array<{ label: string; action: () => void }>
}

interface GlobalSearchModalProps {
  isOpen: boolean
  onClose: () => void
  onNavigate?: (page: string, id?: string) => void
}

const mockResults: SearchResult[] = [
  {
    id:"1",
    type:"candidate",
    title:"João Silva",
    subtitle:"Frontend Developer",
    description:"React, TypeScript, 5+ anos de experiência",
    metadata: {
      status:"Entrevista agendada",
      location:"São Paulo, SP",
      score: 95
    }
  },
  {
    id:"2",
    type:"candidate",
    title:"Maria Santos",
    subtitle:"UX Designer",
    description:"Figma, Design Systems, Portfolio completo",
    metadata: {
      status:"Triagem aprovada",
      location:"Rio de Janeiro, RJ",
      score: 88
    }
  },
  {
    id:"3",
    type:"job",
    title:"Desenvolvedor Full Stack Sênior",
    subtitle:"Vaga #FS-2024-001",
    description:"React, Node.js, TypeScript - Regime CLT",
    metadata: {
      status:"Ativa",
      date:"Publicada há 2 dias"
    }
  },
  {
    id:"4",
    type:"conversation",
    title:"Análise de CVs React",
    subtitle:"Chat com LIA - Hoje",
    description:"Discussão sobre candidatos para vaga de Frontend",
    metadata: {
      date:"14:30"
    }
  },
  {
    id:"5",
    type:"document",
    title:"Relatório de Diversidade Q3",
    subtitle:"Indicadores",
    description:"Métricas de contratação e análise demográfica",
    metadata: {
      date:"Semana passada"
    }
  },
  {
    id:"6",
    type:"automation",
    title:"Triagem Automática React",
    subtitle:"Automação ativa",
    description:"Filtra candidatos com experiência em React/TypeScript",
    metadata: {
      status:"Ativa",
      priority:"high"
    }
  }
]

const aiSuggestionsByCategory: Record<string, string[]> = {
  all: ["Candidatos React com 5+ anos","Vagas abertas em São Paulo","Últimas conversas sobre UX Designer","Relatórios de performance mensal","Automações de follow-up ativas","Configurações de notificação"
  ],
  candidate: ["Candidatos React sênior","Designers com experiência em Figma","Ativos localizados em São Paulo","Nota LIA acima de 80","Contratados nos últimos 30 dias","Com entrevista agendada","Backend Python ou Node.js","Disponíveis para início imediato"
  ],
  job: ["Vagas abertas com urgência","Posições de Tech em São Paulo","Publicadas esta semana","Com mais de 10 candidatos","Próximas do deadline","Sem candidatos ativos","Vagas remotas disponíveis","Posições de liderança"
  ],
  conversation: ["Conversas sobre triagem de candidatos","Análises de perfil recentes","Discussões sobre vagas específicas","Relatórios solicitados à LIA","Conversas de hoje","Feedback de entrevistas","Comparações de candidatos","Sugestões de sourcing"
  ],
  document: ["Relatórios de diversidade","Performance mensal de recrutamento","Análises de funil por vaga","Templates de email ativos","Métricas de time-to-hire","Relatórios de conversão","Análises de custo por contratação","Benchmarks de mercado"
  ],
  automation: ["Triagens automáticas ativas","Follow-ups configurados","Alertas de candidatos ideais","Notificações de deadline","Sync automático com ATS","Relatórios programados","Lembretes de entrevista","Workflows de onboarding"
  ]
}

export function GlobalSearchModal({ isOpen, onClose, onNavigate }: GlobalSearchModalProps) {
  const [query, setQuery] = useState("")
  const [results, setResults] = useState<SearchResult[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedType, setSelectedType] = useState<string>("all")
  const [showAISuggestions, setShowAISuggestions] = useState(true)
  const router = useRouter()
  const locale = useLocale()
  const { data: actionCatalog } = useCommandCatalog()

  // Fase 2 Cmd+K: catálogo de comandos = navegação (Fase 1, canonical-pages)
  // + ações (Fase 2, capability_map). Navegação → router.push; ação → LIA.
  const commandList = [
    ...navigationCatalog(locale).map((n) => ({
      id: `nav-${n.page}`,
      label: `Ir para ${n.label}`,
      hint: "Navegar",
      icon: Compass,
      run: () => router.push(n.url),
    })),
    ...(actionCatalog ?? []).map((a) => ({
      id: `action-${a.intent}`,
      label: a.label,
      hint: a.requires_confirmation ? "Confirma na tela" : "Pedir à LIA",
      icon: Sparkles,
      run: () =>
        window.dispatchEvent(
          new CustomEvent("lia:prefill-message", { detail: { message: a.label } }),
        ),
    })),
  ]
  const filteredCommands = query.trim()
    ? commandList.filter((c) => c.label.toLowerCase().includes(query.toLowerCase()))
    : commandList
  const inputRef = useRef<HTMLInputElement>(null)

  const searchTypes = [
    { id:"all", label:"Todos", icon: Search, count: results.length },
    { id:"candidate", label:"Candidatos", icon: User, count: results.filter(r => r.type ==="candidate").length },
    { id:"job", label:"Vagas", icon: Briefcase, count: results.filter(r => r.type ==="job").length },
    { id:"conversation", label:"Conversas", icon: MessageSquare, count: results.filter(r => r.type ==="conversation").length },
    { id:"document", label:"Documentos", icon: FileText, count: results.filter(r => r.type ==="document").length },
    { id:"automation", label:"Automações", icon: Zap, count: results.filter(r => r.type ==="automation").length },
    { id:"command", label:"Comandos", icon: Compass, count: commandList.length }
  ]

  // Simulate search with debounce
  useEffect(() => {
    if (!query.trim()) {
      setResults([])
      setShowAISuggestions(true)
      return
    }

    setShowAISuggestions(false)
    setIsLoading(true)

    const searchTimeout = setTimeout(() => {
      // Simulate API call
      const filteredResults = mockResults.filter(result => {
        const matchesQuery =
          result.title.toLowerCase().includes(query.toLowerCase()) ||
          result.subtitle.toLowerCase().includes(query.toLowerCase()) ||
          result.description.toLowerCase().includes(query.toLowerCase())

        const matchesType = selectedType ==="all" || result.type === selectedType

        return matchesQuery && matchesType
      })

      setResults(filteredResults)
      setIsLoading(false)
    }, 300)

    return () => clearTimeout(searchTimeout)
  }, [query, selectedType])

  // Focus input when modal opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const handleResultClick = (result: SearchResult) => {
    if (onNavigate) {
      switch (result.type) {
        case"candidate":
          onNavigate("Candidatos", result.id)
          break
        case"job":
          onNavigate("Vagas", result.id)
          break
        case"conversation":
          onNavigate("Chat com LIA", result.id)
          break
        case"document":
          onNavigate("Indicadores", result.id)
          break
        case"automation":
          onNavigate("Configurações", result.id)
          break
        default:
          break
      }
    }
    onClose()
  }

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion)
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case"candidate": return User
      case"job": return Briefcase
      case"conversation": return MessageSquare
      case"document": return FileText
      case"automation": return Zap
      case"setting": return Settings
      default: return Search
    }
  }

  const getStatusColor = (status?: string, type?: string) => {
    if (!status) return"bg-lia-bg-tertiary text-lia-text-primary"

    if (type ==="candidate") {
      switch (status) {
        case"Entrevista agendada": return""
        case"Triagem aprovada": return""
        case"Processo finalizado": return"bg-lia-bg-tertiary text-lia-text-primary"
        default: return""
      }
    }

    if (type ==="job") {
      return status ==="Ativa" ?"" :"bg-lia-bg-tertiary text-lia-text-primary"
    }

    return"bg-lia-bg-tertiary text-lia-text-primary"
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-lia-overlay z-50 flex items-start justify-center pt-16">
      <div 
        className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl w-full max-w-2xl max-h-[70vh] overflow-hidden border border-lia-border-subtle dark:border-lia-border-subtle"
       
      >
        {/* Header */}
        <div className="p-3 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-t-xl">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Buscar candidatos, vagas, conversas..."
                className="w-full pl-9 pr-4 py-2.5 text-sm border border-lia-border-subtle dark:border-lia-border-subtle rounded-lg bg-lia-bg-secondary dark:bg-lia-bg-secondary text-lia-text-primary focus:outline-none focus:ring-1 focus:ring-lia-border-default dark:focus:ring-lia-border-medium focus:border-lia-border-default dark:focus:border-lia-border-medium placeholder:text-lia-text-secondary"
               
              />
              {isLoading && (
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                  <div className="w-3.5 h-3.5 border-2 border-lia-border-medium border-t-transparent rounded-full animate-spin motion-reduce:animate-none"></div>
                </div>
              )}
            </div>
            <Button variant="ghost" size="sm" onClick={onClose} className="h-8 w-8 p-0 text-lia-text-secondary hover:text-lia-text-secondary">
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Filter Tabs */}
          <div className="flex items-center gap-1.5 mt-3 overflow-x-auto">
            {searchTypes.map((type) => (
              <button
                key={type.id}
                onClick={() => setSelectedType(type.id)}
                className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs whitespace-nowrap transition-colors motion-reduce:transition-none ${
 selectedType === type.id
                    ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text'
                    : 'hover:bg-lia-bg-tertiary dark:hover:bg-lia-btn-primary-hover text-lia-text-secondary'
                }`}
              >
                <type.icon className="w-3.5 h-3.5" />
                {type.label}
                {type.count > 0 && (
                  <span className="text-micro px-1 py-0.5 rounded-full bg-lia-interactive-active dark:bg-lia-bg-elevated text-lia-text-secondary">
                    {type.count}
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="max-h-[340px] overflow-y-auto bg-lia-bg-secondary dark:bg-lia-bg-primary/50">
          {/* Fase 2 Cmd+K: aba Comandos (navegação + ações) */}
          {selectedType === "command" && (
            <div className="p-3 space-y-1">
              <div className="flex items-center gap-2 mb-2">
                <Compass className="w-3.5 h-3.5 text-wedo-cyan" />
                <span className="text-xs font-medium text-lia-text-primary">Comandos da LIA</span>
              </div>
              {filteredCommands.map((c) => {
                const Icon = c.icon
                return (
                  <button
                    key={c.id}
                    onClick={() => { c.run(); onClose() }}
                    className="w-full flex items-center gap-2 p-2 text-left text-sm text-lia-text-primary hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover rounded-lg transition-colors motion-reduce:transition-none border border-transparent hover:border-lia-border-subtle"
                  >
                    <Icon className="w-3.5 h-3.5 text-lia-text-secondary shrink-0" />
                    <span className="flex-1 truncate">{c.label}</span>
                    <span className="text-xs text-lia-text-secondary">{c.hint}</span>
                  </button>
                )
              })}
              {filteredCommands.length === 0 && (
                <p className="text-xs text-lia-text-secondary p-2">Nenhum comando para &quot;{query}&quot;.</p>
              )}
            </div>
          )}
          {/* AI Suggestions */}
          {showAISuggestions && selectedType !== "command" && (
            <div className="p-3">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
                <span className="text-xs font-medium text-lia-text-primary">
                  Sugestões da LIA {selectedType !=="all" && `para ${searchTypes.find(t => t.id === selectedType)?.label}`}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-1">
                {(aiSuggestionsByCategory[selectedType] || aiSuggestionsByCategory.all).map((suggestion, index) => (
                  <button
                    key={suggestion}
                    onClick={() => handleSuggestionClick(suggestion)}
                    className="flex items-center gap-2 p-2 text-left text-xs text-lia-text-secondary hover:bg-lia-bg-primary dark:hover:bg-lia-btn-primary-hover rounded-lg transition-colors motion-reduce:transition-none border border-transparent hover:border-lia-border-subtle dark:hover:border-lia-border-strong"
                  >
                    <ArrowRight className="w-3 h-3 opacity-40" />
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Search Results */}
          {results.length > 0 && selectedType !== "command" && (
            <div className="p-4 space-y-2">
              {results.map((result) => {
                const IconComponent = getTypeIcon(result.type)
                return (
                  <Card
                    key={result.id}
                    className="hover:transition-shadow cursor-pointer"
                    onClick={() => handleResultClick(result)}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-lia-bg-tertiary dark:bg-lia-bg-elevated rounded-lg flex items-center justify-center flex-shrink-0">
                          <IconComponent className="w-4 h-4 text-lia-text-secondary" />
                        </div>

                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h3 className="font-medium text-lia-text-primary truncate">
                              {result.title}
                            </h3>
                            {result.metadata?.score && (
                              <Chip density="relaxed" variant="neutral" >
                                {result.metadata.score}% match
                              </Chip>
                            )}
                          </div>

                          <p className="text-sm text-lia-text-secondary mb-1">
                            {result.subtitle}
                          </p>

                          <p className="text-xs text-lia-text-primary mb-2">
                            {result.description}
                          </p>

                          <div className="flex items-center gap-2 flex-wrap">
                            {result.metadata?.status && (
                              <Chip
                                variant="neutral" muted
                                className={`text-xs ${getStatusColor(result.metadata.status, result.type)}`}
                              >
                                {result.metadata.status}
                              </Chip>
                            )}

                            {result.metadata?.location && (
                              <div className="flex items-center gap-1 text-xs text-lia-text-primary">
                                <MapPin className="w-3 h-3" />
                                {result.metadata.location}
                              </div>
                            )}

                            {result.metadata?.date && (
                              <div className="flex items-center gap-1 text-xs text-lia-text-primary">
                                <Clock className="w-3 h-3" />
                                {result.metadata.date}
                              </div>
                            )}
                          </div>
                        </div>

                        <ChevronRight className="w-4 h-4 text-lia-text-secondary flex-shrink-0" />
                      </div>
                    </CardContent>
                  </Card>
                )
              })}
            </div>
          )}

          {/* No Results */}
          {query && !isLoading && results.length === 0 && selectedType !== "command" && (
            <div className="p-8 text-center">
              <Search className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
              <h3 className="text-lg font-medium text-lia-text-primary mb-2">
                Nenhum resultado encontrado
              </h3>
              <p className="text-sm text-lia-text-secondary mb-4">
                Tente ajustar sua busca ou usar termos diferentes
              </p>
              <Button variant="outline" size="sm" onClick={() => setQuery("")}>
                Limpar busca
              </Button>
            </div>
          )}

          {/* Empty State */}
          {!query && !showAISuggestions && (
            <div className="p-8 text-center">
              <Search className="w-12 h-12 text-lia-text-secondary mx-auto mb-4" />
              <h3 className="text-lg font-medium text-lia-text-primary mb-2">
                Busca Global
              </h3>
              <p className="text-sm text-lia-text-secondary">
                Digite para buscar em candidatos, vagas, conversas e muito mais
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-3 py-2 bg-lia-bg-primary dark:bg-lia-bg-primary rounded-b-xl">
          <div className="flex items-center justify-between text-xs text-lia-text-secondary">
            <div className="flex items-center gap-3">
              <span>↑↓ navegar</span>
              <span>Enter selecionar</span>
              <span>Esc fechar</span>
            </div>
            <div className="flex items-center gap-1">
              <Brain className="w-3 h-3 text-wedo-cyan" />
              <span className="text-lia-text-secondary">LIA</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
