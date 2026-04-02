"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Search,
  Brain,
  Mic,
  Send,
  X,
  Users,
  Filter,
  BarChart3,
  Target,
  Clock,
  Zap,
  FileText,
  MapPin,
  DollarSign
} from "lucide-react"

interface AISearchToggleProps {
  placeholder?: string
  onSearch?: (query: string) => void
  onAISearch?: (query: string, aiResults: Record<string, unknown>) => void
  contextType?: 'candidates' | 'jobs' | 'dashboard' | 'general' | 'indicators'
  inline?: boolean // Novo prop para modo in-line
}

export function AISearchToggle({
  placeholder = "Pergunte à LIA...",
  onSearch,
  onAISearch,
  contextType = 'general',
  inline = false
}: AISearchToggleProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [query, setQuery] = useState("")
  const [isListening, setIsListening] = useState(false)
  const [recentCommands, setRecentCommands] = useState<string[]>([])
  const inputRef = useRef<HTMLInputElement>(null)

  // Sugestões contextuais baseadas na página
  const getContextualSuggestions = () => {
    switch (contextType) {
      case 'candidates':
        return [
          {
            icon: Target,
            title: "Buscar por Perfil",
            description: "Desenvolvedores React sênior em São Paulo",
            command: "Mostre desenvolvedores React sênior em São Paulo com inglês fluente"
          },
          {
            icon: Users,
            title: "Criar Persona",
            description: "Definir perfil padrão Backend Java",
            command: "Crie uma persona para desenvolvedor Backend Java com 5+ anos"
          },
          {
            icon: BarChart3,
            title: "Análise Salarial",
            description: "Faixa salarial UX Designer SP",
            command: "Qual a faixa salarial média para UX Designer em São Paulo?"
          },
          {
            icon: Filter,
            title: "Filtro Inteligente",
            description: "Disponíveis para mudança imediata",
            command: "Filtre candidatos disponíveis para mudança imediata"
          },
          {
            icon: MapPin,
            title: "Mapeamento Organizacional",
            description: "Estrutura de cargos na base",
            command: "Mapeie a estrutura organizacional dos candidatos por cargo e senioridade"
          },
          {
            icon: Clock,
            title: "Pipeline Futuro",
            description: "Candidatos para contratação Q2",
            command: "Crie pipeline de candidatos Backend para contratação no próximo trimestre"
          },
          {
            icon: Users,
            title: "Ações em Lote",
            description: "Adicionar selecionados à vaga",
            command: "Adicione todos os candidatos filtrados à vaga Frontend-001"
          },
          {
            icon: Target,
            title: "Comparar Candidatos",
            description: "Analise diferenças entre perfis",
            command: "Compare Ana Costa e João Silva para vaga UX Designer"
          }
        ]
      case 'jobs':
        return [
          {
            icon: Target,
            title: "Sugerir Candidatos",
            description: "Candidatos ideais para esta vaga",
            command: "Sugira os melhores candidatos para esta vaga"
          },
          {
            icon: BarChart3,
            title: "Análise de Salário",
            description: "Compare com mercado",
            command: "Compare o salário desta vaga com a média do mercado"
          }
        ]
      case 'indicators':
        return [
          {
            icon: BarChart3,
            title: "Análise de Performance",
            description: "Indicadores de recrutamento",
            command: "Mostre tendências de contratação do último trimestre"
          },
          {
            icon: Target,
            title: "Comparar Recrutadores",
            description: "Performance entre recrutadores",
            command: "Compare performance entre recrutadores"
          }
        ]
      default:
        return [
          {
            icon: Search,
            title: "Busca Geral",
            description: "Pesquisar em toda a plataforma",
            command: "Busque informações sobre..."
          }
        ]
    }
  }

  const suggestions = getContextualSuggestions()

  // Comandos recentes mockados (em produção viriam do backend)
  const mockRecentCommands = [
    "Desenvolvedores React em São Paulo",
    "Candidatos com inglês fluente",
    "UX Designers com Figma",
    "Análise salarial Backend",
  ]

  useEffect(() => {
    setRecentCommands(mockRecentCommands)
  }, [])

  const handleExpand = () => {
    setIsExpanded(true)
    setTimeout(() => inputRef.current?.focus(), 100)
  }

  const handleCollapse = () => {
    setIsExpanded(false)
    setQuery("")
  }

  const handleSubmit = (commandText?: string) => {
    const finalQuery = commandText || query
    if (!finalQuery.trim()) return

    // Simular resposta da IA
    const aiResults = {
      type: 'search',
      query: finalQuery,
      suggestions: [
        "Encontrei 15 candidatos correspondentes",
        "Aplicando filtros inteligentes...",
        "Analisando perfis semelhantes..."
      ]
    }

    onAISearch?.(finalQuery, aiResults)
    onSearch?.(finalQuery)

    // Adicionar aos comandos recentes
    if (!recentCommands.includes(finalQuery)) {
      setRecentCommands(prev => [finalQuery, ...prev.slice(0, 3)])
    }

    setQuery("")
    setIsExpanded(false)
  }

  const handleVoiceInput = () => {
    setIsListening(!isListening)
    // Aqui seria implementada a funcionalidade de reconhecimento de voz
    if (!isListening) {
      setTimeout(() => {
        setIsListening(false)
        setQuery("Buscar desenvolvedores React sênior")
      }, 2000)
    }
  }

  if (!isExpanded) {
    // Versão compacta - agora funciona tanto para modal quanto inline
    return (
      <div className="relative w-full max-w-md">
        <div
          onClick={handleExpand}
          className="flex items-center gap-3 px-4 py-2.5 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md cursor-pointer transition-colors motion-reduce:transition-none duration-200"
        >
          <Brain className="w-4 h-4 text-status-success dark:text-status-success" />
          <span className="text-sm text-lia-text-primary flex-1">
            {placeholder}
          </span>
          <div className="flex items-center gap-2">
            <Brain className="w-4 h-4 text-status-success dark:text-status-success" />
            <span className="text-xs text-status-success dark:text-status-success font-medium">LIA</span>
          </div>
        </div>
      </div>
    )
  }

  // Versão expandida - inline ou modal baseado no prop
  if (inline) {
    return (
      <div className="w-full">
        {/* Versão expandida in-line */}
        <div className="bg-status-success/10 dark:bg-status-success/20 rounded-xl">

          {/* Header compacto */}
          <div className="flex items-center justify-between p-4">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-status-success rounded-md flex items-center justify-center">
                <Brain className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-status-success dark:text-status-success text-sm">
                  Assistente LIA
                </h3>
                <p className="text-xs text-status-success dark:text-status-success">
                  Comando inteligente para banco de talentos
                </p>
              </div>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCollapse}
              className="text-status-success hover:text-status-success dark:text-status-success dark:hover:text-status-success"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Input Principal */}
          <div className="p-4">
            <div className="flex items-center gap-3 p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md">
              <Brain className="w-4 h-4 text-status-success" />
              <input
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Digite seu comando ou escolha uma sugestão abaixo..."
                className="flex-1 border-0 focus:ring-0 focus:outline-none text-sm bg-transparent text-lia-text-primary"
                onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
              />
              <Button
                variant="ghost"
                size="sm"
                onClick={handleVoiceInput}
                className={`${isListening ? 'text-status-error' : 'text-status-success'}`}
              >
                <Mic className={`w-4 h-4 ${isListening ? 'animate-pulse motion-reduce:animate-none' : ''}`} />
              </Button>
              <Button
                onClick={() => handleSubmit()}
                disabled={!query.trim()}
                className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active px-3 py-1.5 text-sm"
              >
                <Send className="w-3 h-3" />
              </Button>
            </div>
          </div>

          {/* Sugestões Contextuais - Layout Compacto */}
          <div className="px-4 pb-4">
            <h4 className="text-sm font-medium text-status-success dark:text-status-success mb-3">
              💡 Sugestões Rápidas
            </h4>
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
              {suggestions.slice(0, 8).map((suggestion, index) => (
                <button
                  key={suggestion.title}
                  onClick={() => handleSubmit(suggestion.command)}
                  className="text-left p-3 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none duration-200 group"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <suggestion.icon className="w-4 h-4 text-status-success group-hover:text-status-success" />
                    <span className="font-medium text-status-success dark:text-status-success text-xs">
                      {suggestion.title}
                    </span>
                  </div>
                  <p className="text-xs text-status-success dark:text-status-success line-clamp-2">
                    {suggestion.description}
                  </p>
                </button>
              ))}
            </div>
          </div>

          {/* Comandos Recentes - Linha Horizontal */}
          {recentCommands.length > 0 && (
            <div className="px-4 pb-4">
              <h4 className="text-sm font-medium text-status-success dark:text-status-success mb-2">
                🕐 Recentes
              </h4>
              <div className="flex gap-2 overflow-x-auto">
                {recentCommands.map((command, index) => (
                  <button
                    key={`cmd-${index}`}
                    onClick={() => handleSubmit(command)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success rounded-md text-xs hover:bg-status-success/20 dark:hover:bg-status-success/50 transition-colors motion-reduce:transition-none whitespace-nowrap"
                  >
                    <Clock className="w-3 h-3" />
                    {command}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Footer Compacto */}
          <div className="px-4 py-2 bg-status-success/15/50 dark:bg-status-success/20 rounded-b-2xl">
            <div className="flex items-center justify-between text-xs text-status-success dark:text-status-success">
              <span>💡 Use linguagem natural</span>
              <span>⌨️ Enter para enviar</span>
            </div>
          </div>

        </div>
      </div>
    )
  }

  // Modal expansivo (mantém funcionalidade existente para outros contextos)
  return (
    <div className="fixed inset-0 bg-lia-overlay backdrop-blur-sm z-50 flex items-start justify-center pt-20">
      <div className="bg-status-success/10 dark:bg-status-success/20 rounded-xl w-full max-w-4xl mx-4">

        {/* Header */}
        <div className="flex items-center justify-between p-6">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-status-success rounded-md flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-status-success dark:text-status-success">
                Assistente LIA
              </h3>
              <p className="text-sm text-status-success dark:text-status-success">
                Comando inteligente para banco de talentos
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCollapse}
            className="text-status-success hover:text-status-success dark:text-status-success dark:hover:text-status-success"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Input Principal */}
        <div className="p-6">
          <div className="flex items-center gap-3 p-4 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md">
            <Brain className="w-5 h-5 text-status-success" />
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Digite seu comando ou escolha uma sugestão abaixo..."
              className="flex-1 border-0 focus:ring-0 focus:outline-none text-base bg-transparent text-lia-text-primary"
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={handleVoiceInput}
              className={`${isListening ? 'text-status-error' : 'text-status-success'}`}
            >
              <Mic className={`w-5 h-5 ${isListening ? 'animate-pulse motion-reduce:animate-none' : ''}`} />
            </Button>
            <Button
              onClick={() => handleSubmit()}
              disabled={!query.trim()}
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* Sugestões Contextuais */}
        <div className="px-6 pb-4">
          <h4 className="text-sm font-medium text-status-success dark:text-status-success mb-3">
            Sugestões para Banco de Talentos
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {suggestions.map((suggestion, index) => (
              <button
                key={suggestion.title}
                onClick={() => handleSubmit(suggestion.command)}
                className="text-left p-4 bg-lia-bg-primary dark:bg-lia-bg-secondary rounded-md transition-colors motion-reduce:transition-none duration-200 group"
              >
                <div className="flex items-center gap-3 mb-2">
                  <suggestion.icon className="w-5 h-5 text-status-success group-hover:text-status-success" />
                  <span className="font-medium text-status-success dark:text-status-success text-sm">
                    {suggestion.title}
                  </span>
                </div>
                <p className="text-xs text-status-success dark:text-status-success mb-2">
                  {suggestion.description}
                </p>
                <p className="text-xs text-lia-text-primary italic">
                  "{suggestion.command}"
                </p>
              </button>
            ))}
          </div>
        </div>

        {/* Comandos Recentes */}
        {recentCommands.length > 0 && (
          <div className="px-6 pb-6">
            <h4 className="text-sm font-medium text-status-success dark:text-status-success mb-3">
              Comandos Recentes
            </h4>
            <div className="flex flex-wrap gap-2">
              {recentCommands.map((command, index) => (
                <button
                  key={`cmd-${index}`}
                  onClick={() => handleSubmit(command)}
                  className="inline-flex items-center gap-2 px-3 py-1.5 bg-status-success/15 dark:bg-status-success/30 text-status-success dark:text-status-success rounded-md text-sm hover:bg-status-success/20 dark:hover:bg-status-success/50 transition-colors motion-reduce:transition-none"
                >
                  <Clock className="w-3 h-3" />
                  {command}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="px-6 py-4 bg-status-success/15/50 dark:bg-status-success/20 rounded-b-2xl">
          <div className="flex items-center justify-between text-xs text-status-success dark:text-status-success">
            <span>💡 Dica: Use linguagem natural - "Mostre desenvolvedores React em SP"</span>
            <div className="flex items-center gap-4">
              <span>🎤 Pressione para falar</span>
              <span>⌨️ Enter para enviar</span>
            </div>
          </div>
        </div>

      </div>
    </div>
  )
}
