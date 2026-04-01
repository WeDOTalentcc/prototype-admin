"use client"

import { useState, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Search, Plus, Star, Play, Edit, Trash2, Copy, Share2,
  Filter, TrendingUp, Clock, Users, BookOpen, Zap,
  Archive, MoreVertical, Eye, Settings, Brain,
  FileText, Target, Calendar, Mail, BarChart3
} from "lucide-react"

// Interface para Templates
interface CommandTemplate {
  id: string
  name: string
  description: string
  category: 'search' | 'communication' | 'workflow' | 'analysis'
  command: string
  filters?: Record<string, unknown>
  actions: string[]
  createdBy: string
  isShared: boolean
  usageCount: number
  successRate: number
  createdAt: Date
  updatedAt: Date
  tags: string[]
  estimatedTime: number // segundos economizados
}

// Mock de templates iniciais
const mockTemplates: CommandTemplate[] = [
  {
    id: 'template-1',
    name: 'Devs React Sênior SP',
    description: 'Busca desenvolvedores React sênior em São Paulo com 5+ anos de experiência',
    category: 'search',
    command: 'Buscar desenvolvedores React sênior em São Paulo com 5+ anos de experiência e inglês fluente',
    filters: {
      skills: ['React', 'TypeScript', 'Node.js'],
      seniority: ['Sênior'],
      locations: ['São Paulo, SP'],
      years_experience: ['6-10 anos', '10+ anos'],
      spoken_languages: ['Inglês']
    },
    actions: ['filter_react', 'filter_senior_sp', 'filter_english'],
    createdBy: 'Ana Silva',
    isShared: true,
    usageCount: 47,
    successRate: 92,
    createdAt: new Date('2024-12-01'),
    updatedAt: new Date('2024-12-15'),
    tags: ['frontend', 'react', 'senior'],
    estimatedTime: 180
  },
  {
    id: 'template-2',
    name: 'Convite Padrão Frontend',
    description: 'Email personalizado para desenvolvedores frontend com agendamento automático',
    category: 'communication',
    command: 'Enviar convite personalizado para vaga de Frontend Developer com agendamento para próxima semana',
    actions: ['send_individual_email', 'schedule_interview', 'add_priority'],
    createdBy: 'Carlos Mendes',
    isShared: false,
    usageCount: 23,
    successRate: 87,
    createdAt: new Date('2024-11-20'),
    updatedAt: new Date('2024-12-10'),
    tags: ['email', 'frontend', 'agendamento'],
    estimatedTime: 300
  },
  {
    id: 'template-3',
    name: 'Pipeline UX Designer',
    description: 'Workflow completo para candidatos UX: portfolio → teste → entrevista',
    category: 'workflow',
    command: 'Candidatos UX com portfolio, enviar teste de usabilidade e agendar apresentação',
    actions: ['filter_design', 'send_test', 'schedule_interview', 'create_shortlist'],
    createdBy: 'Maria Santos',
    isShared: true,
    usageCount: 15,
    successRate: 94,
    createdAt: new Date('2024-11-15'),
    updatedAt: new Date('2024-12-05'),
    tags: ['ux', 'design', 'workflow'],
    estimatedTime: 420
  },
  {
    id: 'template-4',
    name: 'Relatório Mensal Tech',
    description: 'Análise completa de candidatos tech do mês com métricas de conversão',
    category: 'analysis',
    command: 'Gerar relatório mensal de candidatos tech com métricas de conversão e insights',
    actions: ['group_analysis', 'export_candidates', 'generate_report'],
    createdBy: 'Ana Silva',
    isShared: true,
    usageCount: 8,
    successRate: 100,
    createdAt: new Date('2024-10-30'),
    updatedAt: new Date('2024-12-01'),
    tags: ['relatório', 'tech', 'análise'],
    estimatedTime: 600
  }
]

export function TemplatesPage() {
  const [templates, setTemplates] = useState<CommandTemplate[]>(mockTemplates)
  const [searchTerm, setSearchTerm] = useState("")
  const [selectedCategory, setSelectedCategory] = useState<string>("all")
  const [sortBy, setSortBy] = useState<'usage' | 'recent' | 'success'>('usage')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [editingTemplate, setEditingTemplate] = useState<CommandTemplate | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  // Carregar templates do localStorage
  useEffect(() => {
    const savedTemplates = localStorage.getItem('lia-templates')
    if (savedTemplates) {
      try {
        const parsed = JSON.parse(savedTemplates).map((template: Record<string, unknown>) => ({
          ...template,
          // @ts-ignore TODO: fix type
          createdAt: new Date(template.createdAt),
          // @ts-ignore TODO: fix type
          updatedAt: new Date(template.updatedAt)
        }))
        setTemplates(parsed)
      } catch (error) {
      }
    }
  }, [])

  // Salvar templates no localStorage
  const saveTemplates = (updatedTemplates: CommandTemplate[]) => {
    localStorage.setItem('lia-templates', JSON.stringify(updatedTemplates))
    setTemplates(updatedTemplates)
  }

  // Filtrar e ordenar templates
  const filteredTemplates = useMemo(() => {
    const filtered = templates.filter(template => {
      const matchesSearch = searchTerm === "" ||
        template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
        template.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))

      const matchesCategory = selectedCategory === "all" || template.category === selectedCategory

      return matchesSearch && matchesCategory
    })

    // Ordenação (criar cópia para não mutar)
    return [...filtered].sort((a, b) => {
      switch (sortBy) {
        case 'usage':
          return b.usageCount - a.usageCount
        case 'recent':
          return b.updatedAt.getTime() - a.updatedAt.getTime()
        case 'success':
          return b.successRate - a.successRate
        default:
          return 0
      }
    })
  }, [templates, searchTerm, selectedCategory, sortBy])

  // Estatísticas
  const stats = useMemo(() => {
    const totalUsage = templates.reduce((sum, t) => sum + t.usageCount, 0)
    const avgSuccessRate = templates.reduce((sum, t) => sum + t.successRate, 0) / templates.length
    const totalTimeSaved = templates.reduce((sum, t) => sum + (t.usageCount * t.estimatedTime), 0)
    const sharedTemplates = templates.filter(t => t.isShared).length

    return {
      total: templates.length,
      totalUsage,
      avgSuccessRate: Math.round(avgSuccessRate),
      totalTimeSaved: Math.round(totalTimeSaved / 3600), // em horas
      sharedTemplates
    }
  }, [templates])

  // Executar template (redirecionar para Funil de Talentos)
  const executeTemplate = (template: CommandTemplate) => {
    // Incrementar contador de uso
    const updatedTemplates = templates.map(t =>
      t.id === template.id
        ? { ...t, usageCount: t.usageCount + 1, updatedAt: new Date() }
        : t
    )
    saveTemplates(updatedTemplates)

    // Salvar template para execução na LIA
    sessionStorage.setItem('lia-execute-template', JSON.stringify(template))

    // Redirecionar para Funil de Talentos
    window.location.href = '/?page=candidates&execute-template=' + template.id
  }

  // Duplicar template
  const duplicateTemplate = (template: CommandTemplate) => {
    const newTemplate: CommandTemplate = {
      ...template,
      id: `template-${Date.now()}`,
      name: `${template.name} (Cópia)`,
      createdBy: 'Você',
      isShared: false,
      usageCount: 0,
      createdAt: new Date(),
      updatedAt: new Date()
    }

    saveTemplates([...templates, newTemplate])
  }

  // Deletar template
  const deleteTemplate = (templateId: string) => {
    if (confirm('Tem certeza que deseja excluir este template?')) {
      const updatedTemplates = templates.filter(t => t.id !== templateId)
      saveTemplates(updatedTemplates)
    }
  }

  // Ícones por categoria
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'search': return <Search className="w-4 h-4" />
      case 'communication': return <Mail className="w-4 h-4" />
      case 'workflow': return <Zap className="w-4 h-4" />
      case 'analysis': return <BarChart3 className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  // Cores por categoria
  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'search': return 'bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-primary dark:text-lia-text-primary border-lia-border-default dark:border-lia-border-default'
      case 'communication': return 'bg-status-success/15 text-status-success border-status-success/30'
      case 'workflow': return 'bg-wedo-purple/15 text-wedo-purple border-wedo-purple/30'
      case 'analysis': return 'bg-wedo-orange/15 text-wedo-orange border-wedo-orange/30'
      default: return 'bg-gray-100 text-lia-text-primary dark:text-lia-text-primary border-lia-border-subtle'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold font-sans text-lia-text-primary dark:text-lia-text-primary mb-2 flex items-center gap-2">
            <Brain className="w-6 h-6 text-wedo-cyan" />
            Templates LIA
          </h1>
          <p className="text-lia-text-secondary dark:text-lia-text-tertiary">
            Gerencie comandos personalizados e acelere seu workflow de recrutamento
          </p>
        </div>
        <Button
          onClick={() => setShowCreateModal(true)}
          className="gap-2"
        >
          <Plus className="w-4 h-4" />
          Novo Template
        </Button>
      </div>

      {/* Estatísticas */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <BookOpen className="w-4 h-4 text-lia-text-secondary dark:text-lia-text-tertiary" />
              <div>
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Templates</p>
                <p className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-status-success" />
              <div>
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Execuções</p>
                <p className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{stats.totalUsage}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-wedo-purple" />
              <div>
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Taxa Sucesso</p>
                <p className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{stats.avgSuccessRate}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-wedo-orange" />
              <div>
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Tempo Poupado</p>
                <p className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{stats.totalTimeSaved}h</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-wedo-cyan" />
              <div>
                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">Compartilhados</p>
                <p className="text-xl font-semibold text-lia-text-primary dark:text-lia-text-primary">{stats.sharedTemplates}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filtros e Busca */}
      <div className="flex flex-col lg:flex-row gap-4 mb-6">
        <div className="flex-1">
          <Input
            placeholder="Buscar templates..."
            value={searchTerm}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchTerm(e.target.value)}
            className="w-full"
          />
        </div>

        <div className="flex gap-2">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary dark:text-lia-text-primary"
          >
            <option value="all">Todas Categorias</option>
            <option value="search">🔍 Busca</option>
            <option value="communication">📧 Comunicação</option>
            <option value="workflow">⚡ Workflows</option>
            <option value="analysis">📊 Análises</option>
          </select>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as 'usage' | 'recent' | 'success')}
            className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-elevated text-lia-text-primary dark:text-lia-text-primary"
          >
            <option value="usage">Mais Usados</option>
            <option value="recent">Mais Recentes</option>
            <option value="success">Maior Sucesso</option>
          </select>
        </div>
      </div>

      {/* Lista de Templates */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {filteredTemplates.map((template) => (
          <Card key={template.id} className="hover:transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={`text-xs px-2 py-1 ${getCategoryColor(template.category)}`}>
                      {getCategoryIcon(template.category)}
                      <span className="ml-1 capitalize">{template.category}</span>
                    </Badge>
                    {template.isShared && (
                      <Badge variant="outline" className="text-xs">
                        <Users className="w-3 h-3 mr-1" />
                        Compartilhado
                      </Badge>
                    )}
                  </div>
                  <CardTitle className="text-lg">{template.name}</CardTitle>
                  <p className="text-sm text-lia-text-primary dark:text-lia-text-primary mt-1">
                    {template.description}
                  </p>
                </div>

                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreVertical className="w-4 h-4" />
                </Button>
              </div>
            </CardHeader>

            <CardContent>
              {/* Tags */}
              <div className="flex flex-wrap gap-1 mb-3">
                {template.tags.map((tag, index) => (
                  <Badge key={tag} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>

              {/* Métricas */}
              <div className="grid grid-cols-3 gap-2 text-center mb-4">
                <div>
                  <p className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary">{template.usageCount}</p>
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">Usos</p>
                </div>
                <div>
                  <p className="text-lg font-semibold text-status-success">{template.successRate}%</p>
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">Sucesso</p>
                </div>
                <div>
                  <p className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary">{Math.round(template.estimatedTime/60)}min</p>
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">Economia</p>
                </div>
              </div>

              {/* Ações */}
              <div className="flex gap-2">
                <Button
                  onClick={() => executeTemplate(template)}
                  className="flex-1 gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200"
                  size="sm"
                >
                  <Play className="w-3 h-3" />
                  Executar
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => duplicateTemplate(template)}
                  className="gap-2"
                >
                  <Copy className="w-3 h-3" />
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setEditingTemplate(template)}
                  className="gap-2"
                >
                  <Edit className="w-3 h-3" />
                </Button>
              </div>

              {/* Info adicional */}
              <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between text-xs text-lia-text-primary dark:text-lia-text-primary">
                  <span>Por {template.createdBy}</span>
                  <span>{template.updatedAt.toLocaleDateString()}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <Brain className="w-12 h-12 text-wedo-cyan mx-auto mb-4" />
            <h3 className="text-lg font-medium text-lia-text-primary dark:text-lia-text-primary mb-2">
              Nenhum template encontrado
            </h3>
            <p className="text-lia-text-primary dark:text-lia-text-primary mb-4">
              {searchTerm || selectedCategory !== "all"
                ? "Tente ajustar os filtros de busca"
                : "Crie seu primeiro template para acelerar seu workflow"
              }
            </p>
            <Button onClick={() => setShowCreateModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Criar Primeiro Template
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
