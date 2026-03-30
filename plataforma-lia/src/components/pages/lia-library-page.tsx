'use client'

import React, { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  BookOpen, Search, Users, Star, Copy, MessageCircle,
  Target, Zap, BarChart3, MessageSquare, Brain,
  ArrowRight, Calendar, Mail
} from 'lucide-react'

interface Command {
  id: string
  title: string
  command: string
  description: string
  category: string
  usageCount?: number
}

interface LiaLibraryPageProps {
  onNavigate?: (page: string) => void
}

const commands: Command[] = [
  {
    id: '1',
    title: 'Buscar candidatos por stack',
    command: 'Encontre candidatos com experiência em React, Node.js e PostgreSQL com pelo menos 3 anos de experiência',
    description: 'Localiza perfis técnicos específicos com base em tecnologias e tempo de experiência',
    category: 'candidates',
    usageCount: 156
  },
  {
    id: '2',
    title: 'Analisar fit cultural',
    command: 'Analise o perfil do candidato focando em fit cultural para nossa empresa',
    description: 'Avalia compatibilidade cultural e comportamental do candidato',
    category: 'candidates',
    usageCount: 89
  },
  {
    id: '3',
    title: 'Criar descrição de vaga',
    command: 'Crie uma descrição completa para vaga de Product Manager Sênior focando em growth e data-driven',
    description: 'Gera descrições de vagas atrativas e precisas',
    category: 'jobs',
    usageCount: 124
  },
  {
    id: '4',
    title: 'Otimizar anúncio LinkedIn',
    command: 'Otimize este anúncio de vaga para maximizar engajamento no LinkedIn',
    description: 'Melhora performance de anúncios em redes sociais',
    category: 'jobs',
    usageCount: 67
  },
  {
    id: '5',
    title: 'Calcular time-to-hire',
    command: 'Calcule o time-to-hire médio do último trimestre',
    description: 'Analisa métricas temporais de recrutamento',
    category: 'indicators',
    usageCount: 45
  },
  {
    id: '6',
    title: 'Analisar funil de conversão',
    command: 'Analise a taxa de conversão do funil de recrutamento atual',
    description: 'Identifica gargalos no processo seletivo',
    category: 'indicators',
    usageCount: 78
  },
  {
    id: '7',
    title: 'Agendar entrevistas em lote',
    command: 'Agende entrevistas para os 5 candidatos finalistas da vaga de Engenheiro de Software',
    description: 'Automatiza agendamento de múltiplas entrevistas',
    category: 'automations',
    usageCount: 92
  },
  {
    id: '8',
    title: 'Enviar feedback negativo',
    command: 'Envie feedback personalizado para candidatos não aprovados na triagem',
    description: 'Automatiza comunicação com candidatos reprovados',
    category: 'communication',
    usageCount: 134
  },
  {
    id: '9',
    title: 'Gerar relatório semanal',
    command: 'Gere um relatório semanal de recrutamento com métricas de performance',
    description: 'Cria relatórios executivos automaticamente',
    category: 'reports',
    usageCount: 56
  },
  {
    id: '10',
    title: 'Comparar candidatos',
    command: 'Compare os 3 finalistas para a vaga de Diretor de Tecnologia',
    description: 'Gera análise comparativa detalhada entre candidatos',
    category: 'candidates',
    usageCount: 101
  },
  {
    id: '11',
    title: 'Sugerir perguntas técnicas',
    command: 'Sugira 10 perguntas técnicas para entrevista de desenvolvedor Python sênior',
    description: 'Gera roteiro de entrevista técnica personalizado',
    category: 'jobs',
    usageCount: 88
  },
  {
    id: '12',
    title: 'Analisar currículo',
    command: 'Analise este currículo e extraia as principais competências e experiências',
    description: 'Extrai informações estruturadas de CVs',
    category: 'candidates',
    usageCount: 203
  }
]

const categories = [
  { value: 'all', label: 'Todos', icon: Brain, color: 'var(--wedo-cyan)', bgColor: 'var(--wedo-cyan-bg-15)' },
  { value: 'candidates', label: 'Candidatos', icon: Users, color: 'var(--gray-500)', bgColor: 'var(--gray-bg-15)' },
  { value: 'jobs', label: 'Vagas', icon: Target, color: 'var(--gray-400)', bgColor: 'var(--gray-bg-10)' },
  { value: 'indicators', label: 'Indicadores', icon: BarChart3, color: 'var(--gray-600)', bgColor: 'var(--gray-600-bg-10)' },
  { value: 'automations', label: 'Automações', icon: Zap, color: 'var(--wedo-orange)', bgColor: 'var(--wedo-orange-bg-15)' },
  { value: 'reports', label: 'Relatórios', icon: Calendar, color: 'var(--gray-600)', bgColor: 'var(--gray-600-bg-10)' },
  { value: 'communication', label: 'Comunicação', icon: Mail, color: 'var(--gray-400)', bgColor: 'var(--gray-bg-10)' }
]

export default function LiaLibraryPage({ onNavigate }: LiaLibraryPageProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [showFavoritesOnly, setShowFavoritesOnly] = useState(false)
  const [favorites, setFavorites] = useState<Set<string>>(new Set())
  const [copiedId, setCopiedId] = useState<string | null>(null)

  useEffect(() => {
    const savedFavorites = localStorage.getItem('liaFavorites')
    if (savedFavorites) {
      setFavorites(new Set(JSON.parse(savedFavorites)))
    }
  }, [])

  useEffect(() => {
    localStorage.setItem('liaFavorites', JSON.stringify(Array.from(favorites)))
  }, [favorites])

  const toggleFavorite = (id: string) => {
    setFavorites(prev => {
      const newFavorites = new Set(prev)
      if (newFavorites.has(id)) {
        newFavorites.delete(id)
      } else {
        newFavorites.add(id)
      }
      return newFavorites
    })
  }

  const copyCommand = (id: string, command: string) => {
    navigator.clipboard.writeText(command)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  const executeCommand = (command: string, title: string) => {
    if (onNavigate) {
      onNavigate('Chat com LIA')
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('lia-execute-command', {
          detail: { command, title }
        }))
      }, 100)
    }
  }

  const handlePromptSubmit = (value: string) => {
    if (onNavigate && value.trim()) {
      onNavigate('Chat com LIA')
      setTimeout(() => {
        window.dispatchEvent(new CustomEvent('lia-library-prompt', {
          detail: { prompt: value }
        }))
      }, 100)
    }
  }

  const handleCategoryClick = (categoryValue: string) => {
    setSelectedCategory(categoryValue)
  }

  const filteredCommands = commands.filter(command => {
    const matchesSearch = command.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      command.command.toLowerCase().includes(searchTerm.toLowerCase()) ||
      command.description.toLowerCase().includes(searchTerm.toLowerCase())

    const matchesCategory = selectedCategory === 'all' || command.category === selectedCategory

    const matchesFavorites = !showFavoritesOnly || favorites.has(command.id)

    return matchesSearch && matchesCategory && matchesFavorites
  })

  const getCategoryInfo = (categoryValue: string) => {
    return categories.find(c => c.value === categoryValue) || categories[0]
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary">
      <div className="p-2.5 max-w-full">

        {/* Header Simplificado */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-xl font-['Open_Sans',sans-serif] font-semibold wedo-text-black mb-1 flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-lia-text-secondary" />
              Biblioteca LIA
            </h1>
            <p className="text-sm font-open-sans wedo-text-gray">
              Repositório de comandos inteligentes para recrutamento
            </p>
          </div>
          <Button
            variant={showFavoritesOnly ? "default" : "outline"}
            onClick={() => setShowFavoritesOnly(!showFavoritesOnly)}
            className="gap-2 h-8 px-3"
          >
            <Star className={`w-4 h-4 ${showFavoritesOnly ? 'fill-current' : ''}`} />
            Favoritos {favorites.size > 0 && `(${favorites.size})`}
          </Button>
        </div>

        {/* Prompt AI-First */}
        <div className="bg-white dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle p-5 mb-5">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full flex items-center justify-center bg-gray-900">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <span className="text-base font-['Open_Sans',sans-serif] font-medium text-lia-text-primary dark:text-lia-text-primary">
              O que você precisa fazer hoje?
            </span>
          </div>
          
          <div className="relative mb-4">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-lia-text-primary" />
            <input
              type="text"
              placeholder="Descreva sua necessidade ou pergunte à LIA..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && searchTerm.trim()) {
                  handlePromptSubmit(searchTerm)
                }
              }}
              className="w-full pl-12 pr-24 py-3 text-sm font-open-sans border border-lia-border-subtle dark:border-lia-border-subtle rounded-md bg-gray-50 dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary placeholder-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-900/20 dark:focus:ring-gray-50/20 focus:border-transparent"
            />
            {searchTerm.trim() && (
              <Button
                size="sm"
                onClick={() => handlePromptSubmit(searchTerm)}
                className="absolute right-2 top-1/2 -translate-y-1/2 h-8 px-3 text-white bg-gray-900"
              >
                <ArrowRight className="w-4 h-4" />
              </Button>
            )}
          </div>

          {/* Chips de Categoria */}
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => {
              const Icon = category.icon
              const isSelected = selectedCategory === category.value
              return (
                <button
                  key={category.value}
                  onClick={() => handleCategoryClick(category.value)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-open-sans font-medium transition-[width,height] ${
                    isSelected
                      ? 'text-white'
                      : 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-tertiary hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                  style={isSelected ? { backgroundColor: category.color } : undefined}
                >
                  <Icon className="w-3.5 h-3.5" />
                  {category.label}
                </button>
              )
            })}
          </div>
        </div>

        {/* Contador de Resultados */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-open-sans text-lia-text-primary dark:text-lia-text-tertiary">
            {filteredCommands.length} comando{filteredCommands.length !== 1 ? 's' : ''} disponíve{filteredCommands.length !== 1 ? 'is' : 'l'}
          </span>
        </div>

        {/* Grid de Cards Compactos */}
        {filteredCommands.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
            {filteredCommands.map((command) => {
              const categoryInfo = getCategoryInfo(command.category)
              const isFavorite = favorites.has(command.id)
              const isCopied = copiedId === command.id

              return (
                <div
                  key={command.id}
                  className="group bg-white dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle p-4 hover:border-lia-border-default dark:hover:border-gray-700 transition-colors"
                  style={{borderLeftWidth: '3px', borderLeftColor: categoryInfo.color}}
                >
                  {/* Header do Card */}
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="text-sm font-['Open_Sans',sans-serif] font-medium text-lia-text-primary dark:text-lia-text-primary leading-tight pr-2">
                      {command.title}
                    </h3>
                    <button
                      onClick={() => toggleFavorite(command.id)}
                      className="shrink-0 p-1 -m-1 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                    >
                      <Star 
                        className={`w-4 h-4 ${isFavorite ? 'fill-current' : ''}`}
                        style={{color: isFavorite ? 'var(--wedo-orange)' : 'var(--gray-400)'}}
                      />
                    </button>
                  </div>

                  {/* Descrição */}
                  <p className="text-xs font-open-sans text-lia-text-primary dark:text-lia-text-tertiary leading-relaxed mb-3 line-clamp-2">
                    {command.description}
                  </p>

                  {/* Footer */}
                  <div className="flex items-center justify-between pt-2 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant="secondary" 
                        className="text-xs px-1.5 py-0 h-5 font-open-sans"
                        style={{backgroundColor: categoryInfo.bgColor, color: categoryInfo.color}}
                      >
                        {categoryInfo.label}
                      </Badge>
                      {command.usageCount && (
                        <span className="text-xs text-lia-text-primary dark:text-lia-text-tertiary">
                          {command.usageCount} usos
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => copyCommand(command.id, command.command)}
                        className="p-1.5 rounded-md hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors opacity-0 group-hover:opacity-100"
                        title="Copiar comando"
                      >
                        <Copy className={`w-3.5 h-3.5 ${isCopied ? 'text-status-success' : 'text-lia-text-primary'}`} />
                      </button>
                      <Button
                        size="sm"
                        onClick={() => executeCommand(command.command, command.title)}
                        className="h-7 px-2.5 text-xs font-open-sans text-white"
                        style={{backgroundColor: categoryInfo.color}}
                      >
                        <MessageCircle className="w-3 h-3 mr-1" />
                        Executar
                      </Button>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        ) : (
          <div className="bg-white dark:bg-lia-bg-primary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle p-12">
            <div className="text-center">
              <div className="mx-auto w-16 h-16 bg-gray-100 dark:bg-lia-bg-secondary rounded-full flex items-center justify-center mb-4">
                <Search className="w-6 h-6 text-lia-text-primary" />
              </div>
              <h3 className="text-base font-['Open_Sans',sans-serif] font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
                Nenhum comando encontrado
              </h3>
              <p className="text-sm font-open-sans text-lia-text-primary dark:text-lia-text-tertiary mb-4">
                Tente ajustar os filtros ou descreva sua necessidade para a LIA
              </p>
              <Button
                onClick={() => {
                  setSelectedCategory('all')
                  setShowFavoritesOnly(false)
                  setSearchTerm('')
                }}
                variant="outline"
                size="sm"
              >
                Limpar filtros
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
