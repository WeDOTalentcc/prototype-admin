"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import {
  Plus, Search, Filter, Edit, Copy, Trash2, Star, StarOff, Eye, Download,
  Brain, Wand2, FileText, Users, Building, MapPin, DollarSign,
  Clock, Target, Zap, BookOpen, TrendingUp, BarChart3, CheckCircle,
  AlertCircle, Info, Lightbulb, Cpu, Globe, X
} from "lucide-react"

interface JobTemplate {
  id: string
  name: string
  department: string
  level: string
  workModel: "presencial" | "híbrido" | "remoto"
  category: "tech" | "design" | "produto" | "marketing" | "vendas" | "rh" | "financeiro"
  isAIGenerated: boolean
  isFavorite: boolean
  usage: number
  successRate: number
  avgTimeToHire: number
  template: {
    title: string
    description: string
    requirements: string[]
    benefits: string[]
    salaryRange: string
    responsibilities: string[]
  }
  aiInsights: {
    marketDemand: "alta" | "média" | "baixa"
    competitiveness: number
    suggestedImprovements: string[]
    predictedApplications: number
  }
  lastUsed: string
  createdBy: "AI" | "user"
  tags: string[]
}

const templates: JobTemplate[] = [
  {
    id: "1",
    name: "UX Designer Sênior - Tech Startup",
    department: "Design",
    level: "Sênior",
    workModel: "híbrido",
    category: "design",
    isAIGenerated: true,
    isFavorite: true,
    usage: 23,
    successRate: 87,
    avgTimeToHire: 28,
    template: {
      title: "UX Designer Sênior",
      description: "Buscamos UX Designer experiente para liderar projetos de produtos digitais inovadores, criando experiências excepcionais que impactem milhões de usuários.",
      requirements: ["5+ anos em UX/UI", "Figma avançado", "Design Systems", "Prototipagem", "Pesquisa de usuário"],
      benefits: ["Vale alimentação R$ 1.200", "Plano de saúde premium", "Home office híbrido", "Day off aniversário"],
      salaryRange: "R$ 8.000 - R$ 12.000",
      responsibilities: ["Liderar projetos de UX", "Criar wireframes e protótipos", "Conduzir pesquisas de usuário", "Colaborar com PMs e Devs"]
    },
    aiInsights: {
      marketDemand: "alta",
      competitiveness: 8.5,
      suggestedImprovements: ["Adicionar menção a metodologias ágeis", "Destacar crescimento profissional"],
      predictedApplications: 180
    },
    lastUsed: "2025-01-18",
    createdBy: "AI",
    tags: ["ux", "design", "startup", "produto"]
  },
  {
    id: "2",
    name: "Desenvolvedor React - Remoto",
    department: "Tecnologia",
    level: "Sênior",
    workModel: "remoto",
    category: "tech",
    isAIGenerated: true,
    isFavorite: false,
    usage: 31,
    successRate: 91,
    avgTimeToHire: 25,
    template: {
      title: "Desenvolvedor React Sênior",
      description: "Desenvolvedor React experiente para trabalhar com arquiteturas modernas e tecnologias de ponta em ambiente 100% remoto.",
      requirements: ["React 18+", "TypeScript", "Next.js", "Node.js", "Testes automatizados"],
      benefits: ["Flexibilidade total", "Equipment allowance", "Cursos e certificações", "Bônus performance"],
      salaryRange: "R$ 10.000 - R$ 15.000",
      responsibilities: ["Desenvolver features", "Code review", "Mentoring júniores", "Arquitetura de soluções"]
    },
    aiInsights: {
      marketDemand: "alta",
      competitiveness: 9.2,
      suggestedImprovements: ["Mencionar stack de testes", "Incluir GraphQL nos requisitos"],
      predictedApplications: 250
    },
    lastUsed: "2025-01-20",
    createdBy: "AI",
    tags: ["react", "frontend", "remoto", "senior"]
  },
  {
    id: "3",
    name: "Product Manager - Fintech",
    department: "Produto",
    level: "Pleno",
    workModel: "presencial",
    category: "produto",
    isAIGenerated: false,
    isFavorite: true,
    usage: 12,
    successRate: 75,
    avgTimeToHire: 35,
    template: {
      title: "Product Manager",
      description: "PM para liderar produtos financeiros digitais, trabalhando com regulamentações e compliance do setor.",
      requirements: ["3+ anos como PM", "Experiência Fintech", "Analytics", "Regulamentações financeiras"],
      benefits: ["Plano de saúde premium", "Previdência privada", "Stock options", "Auxílio educação"],
      salaryRange: "R$ 12.000 - R$ 18.000",
      responsibilities: ["Product roadmap", "Stakeholder management", "Analytics", "Go-to-market"]
    },
    aiInsights: {
      marketDemand: "média",
      competitiveness: 7.8,
      suggestedImprovements: ["Adicionar experiência com APIs", "Mencionar metodologias ágeis"],
      predictedApplications: 95
    },
    lastUsed: "2025-01-15",
    createdBy: "user",
    tags: ["pm", "fintech", "produto", "compliance"]
  }
]

const categories = [
  { id: "all", name: "Todos", icon: FileText },
  { id: "tech", name: "Tecnologia", icon: Cpu },
  { id: "design", name: "Design", icon: Brain },
  { id: "produto", name: "Produto", icon: Target },
  { id: "marketing", name: "Marketing", icon: TrendingUp },
  { id: "vendas", name: "Vendas", icon: BarChart3 },
  { id: "rh", name: "RH", icon: Users },
  { id: "financeiro", name: "Financeiro", icon: DollarSign }
]

export function JobTemplatesPage() {
  const [selectedCategory, setSelectedCategory] = useState("all")
  const [searchTerm, setSearchTerm] = useState("")
  const [showAIGenerator, setShowAIGenerator] = useState(false)
  const [sortBy, setSortBy] = useState<"usage" | "success" | "recent">("usage")

  const filteredTemplates = templates.filter(template => {
    const matchesCategory = selectedCategory === "all" || template.category === selectedCategory
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.template.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))

    return matchesCategory && matchesSearch
  }).sort((a, b) => {
    switch (sortBy) {
      case "usage": return b.usage - a.usage
      case "success": return b.successRate - a.successRate
      case "recent": return new Date(b.lastUsed).getTime() - new Date(a.lastUsed).getTime()
      default: return 0
    }
  })

  const getSuccessColor = (rate: number) => {
    if (rate >= 85) return "text-status-success"
    if (rate >= 70) return "text-status-warning"
    return "text-status-error"
  }

  const getDemandColor = (demand: string) => {
    switch (demand) {
      case "alta": return "bg-status-success/15 text-status-success border-status-success/30"
      case "média": return "bg-status-warning/15 text-status-warning border-status-warning/30"
      case "baixa": return "bg-status-error/15 text-status-error border-status-error/30"
      default: return "bg-gray-100 text-lia-text-primary dark:text-lia-text-primary border-lia-border-subtle"
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-lia-bg-primary">
      <div className="max-w-full mx-auto px-6 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h1 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary mb-1 flex items-center gap-1.5">
                <Brain className="w-6 h-6 text-wedo-cyan" />
                Templates de Vagas com IA
              </h1>
              <p className="text-lia-text-secondary dark:text-lia-text-tertiary">
                Acelere a criação de vagas com templates inteligentes e sugestões da IA
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => setShowAIGenerator(true)}
              >
                <Brain className="w-4 h-4 text-wedo-cyan" />
                Gerar com IA
              </Button>
              <Button className="gap-2">
                <Plus className="w-4 h-4" />
                Novo Template
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-lia-text-secondary">Templates Ativos</p>
                  <p className="text-2xl font-bold text-lia-text-primary">{templates.length}</p>
                  <p className="text-xs text-status-success">+3 este mês</p>
                </div>
                <div className="w-10 h-10 bg-gray-100 dark:bg-lia-bg-secondary rounded-md flex items-center justify-center">
                  <FileText className="w-5 h-5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-lia-text-secondary">Taxa Sucesso Média</p>
                  <p className="text-2xl font-bold text-status-success">
                    {Math.round(templates.reduce((acc, t) => acc + t.successRate, 0) / templates.length)}%
                  </p>
                  <p className="text-xs text-status-success">+5% vs mês anterior</p>
                </div>
                <div className="w-10 h-10 bg-status-success/15 rounded-md flex items-center justify-center">
                  <CheckCircle className="w-5 h-5 text-status-success" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-lia-text-secondary">Templates IA</p>
                  <p className="text-2xl font-bold text-wedo-purple">
                    {templates.filter(t => t.isAIGenerated).length}
                  </p>
                  <p className="text-xs text-wedo-purple">67% do total</p>
                </div>
                <div className="w-10 h-10 bg-wedo-purple/15 rounded-md flex items-center justify-center">
                  <Brain className="w-5 h-5 text-wedo-cyan" />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-lia-text-secondary">Tempo Médio</p>
                  <p className="text-2xl font-bold text-wedo-orange">
                    {Math.round(templates.reduce((acc, t) => acc + t.avgTimeToHire, 0) / templates.length)}d
                  </p>
                  <p className="text-xs text-wedo-orange">para contratação</p>
                </div>
                <div className="w-10 h-10 bg-wedo-orange/15 rounded-md flex items-center justify-center">
                  <Clock className="w-5 h-5 text-wedo-orange" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters and Search */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-col lg:flex-row gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
                  <input
                    type="text"
                    placeholder="Buscar templates por nome, cargo, tags..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
                  />
                </div>
              </div>

              <div className="flex gap-3">
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as Parameters<typeof setSortBy>[0])}
                  className="px-3 py-2 border border-lia-border-default dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-secondary"
                >
                  <option value="usage">Mais Usados</option>
                  <option value="success">Maior Sucesso</option>
                  <option value="recent">Mais Recentes</option>
                </select>

                <Button variant="outline" size="sm" className="gap-2">
                  <Filter className="w-4 h-4" />
                  Filtros
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Categories */}
        <div className="flex items-center gap-2 mb-6 overflow-x-auto">
          {categories.map((category) => (
            <Button
              key={category.id}
              // @ts-ignore TODO: fix type
              variant={selectedCategory === category.id ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedCategory(category.id)}
              className="flex items-center gap-2 whitespace-nowrap"
            >
              <category.icon className="w-4 h-4" />
              {category.name}
            </Button>
          ))}
        </div>

        {/* Templates Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredTemplates.map((template) => (
            <Card key={template.id} className="hover:transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {template.isAIGenerated && (
                      <Badge variant="outline" className="bg-wedo-purple/10 text-wedo-purple border-wedo-purple/30">
                        <Brain className="w-3 h-3 mr-1 text-wedo-cyan" />
                        IA
                      </Badge>
                    )}
                    <Badge variant="outline" className={getDemandColor(template.aiInsights.marketDemand)}>
                      {template.aiInsights.marketDemand} demanda
                    </Badge>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {/* toggle favorite */}}
                    className="h-8 w-8 p-0"
                  >
                    {template.isFavorite ?
                      <Star className="w-4 h-4 text-status-warning fill-current" /> :
                      <StarOff className="w-4 h-4 text-lia-text-secondary" />
                    }
                  </Button>
                </div>

                <CardTitle className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary">
                  {template.name}
                </CardTitle>

                <div className="flex items-center gap-2 text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                  <Building className="w-4 h-4" />
                  <span>{template.department}</span>
                  <span>•</span>
                  <span>{template.level}</span>
                  <Badge variant="outline" className={`text-xs ${
                    template.workModel === 'remoto' ? 'border-lia-border-default dark:border-lia-border-default bg-gray-100 dark:bg-lia-bg-secondary text-lia-text-secondary dark:text-lia-text-tertiary' :
                    template.workModel === 'híbrido' ? 'border-wedo-purple/30 bg-wedo-purple/10 text-wedo-purple' :
                    'border-status-success/30 bg-status-success/10 text-status-success'
                  }`}>
                    {template.workModel}
                  </Badge>
                </div>

                <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary line-clamp-2">
                  {template.template.description}
                </p>
              </CardHeader>

              <CardContent className="pt-0">
                {/* Metrics */}
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center">
                    <div className="text-xs font-bold text-lia-text-primary dark:text-lia-text-primary">{template.usage}</div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">usos</div>
                  </div>
                  <div className="text-center">
                    <div className={`text-xs font-bold ${getSuccessColor(template.successRate)}`}>
                      {template.successRate}%
                    </div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">sucesso</div>
                  </div>
                  <div className="text-center">
                    <div className="text-xs font-bold text-wedo-orange">{template.avgTimeToHire}d</div>
                    <div className="text-xs text-lia-text-primary dark:text-lia-text-primary">tempo</div>
                  </div>
                </div>

                {/* AI Insights */}
                <div className="bg-gray-100 dark:bg-lia-bg-secondary rounded-md p-3 mb-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    <span className="text-sm font-medium text-lia-text-secondary dark:text-lia-text-tertiary/80">Insights da IA</span>
                  </div>
                  <div className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary/80 space-y-1">
                    <div>Previsão: {template.aiInsights.predictedApplications} candidatos</div>
                    <div>Competitividade: {template.aiInsights.competitiveness}/10</div>
                  </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1 mb-4">
                  {template.tags.map((tag, index) => (
                    <Badge key={tag} variant="secondary" className="text-xs">
                      {tag}
                    </Badge>
                  ))}
                </div>

                {/* Actions */}
                <div className="space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    <Button size="sm" variant="outline" className="gap-2">
                      <Eye className="w-3 h-3" />
                      Visualizar
                    </Button>
                    <Button size="sm" variant="outline" className="gap-2">
                      <Copy className="w-3 h-3" />
                      Usar Template
                    </Button>
                  </div>
                  <Button size="sm" variant={"default" as any} className="w-full gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200">
                    <Wand2 className="w-3 h-3" />
                    Criar Vaga
                  </Button>
                </div>

                <div className="text-xs text-lia-text-primary dark:text-lia-text-primary mt-3">
                  Último uso: {new Date(template.lastUsed).toLocaleDateString("pt-BR")}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* AI Generator Modal */}
        {showAIGenerator && (
          <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
            <div className="bg-white dark:bg-lia-bg-secondary rounded-md w-full max-w-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-semibold flex items-center gap-2">
                  <Brain className="w-5 h-5 text-wedo-purple" />
                  Gerador de Templates com IA
                </h3>
                <Button variant="ghost" size="sm" onClick={() => setShowAIGenerator(false)}>
                  <X className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Cargo desejado</label>
                  <input
                    type="text"
                    placeholder="Ex: Desenvolvedor Frontend, UX Designer, Product Manager..."
                    className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Departamento</label>
                    <select className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md">
                      <option>Tecnologia</option>
                      <option>Design</option>
                      <option>Produto</option>
                      <option>Marketing</option>
                      <option>Vendas</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Nível</label>
                    <select className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md">
                      <option>Júnior</option>
                      <option>Pleno</option>
                      <option>Sênior</option>
                      <option>Especialista</option>
                      <option>Lead</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Contexto adicional (opcional)</label>
                  <textarea
                    rows={3}
                    placeholder="Descreva características específicas da empresa, cultura, stack tecnológico..."
                    className="w-full p-3 border border-lia-border-default dark:border-lia-border-default rounded-md"
                  />
                </div>

                <div className="bg-wedo-purple/10 dark:bg-wedo-purple/20 rounded-md p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="w-4 h-4 text-wedo-purple" />
                    <span className="text-sm font-medium text-wedo-purple dark:text-wedo-purple">
                      IA vai gerar automaticamente:
                    </span>
                  </div>
                  <ul className="text-xs text-wedo-purple dark:text-wedo-purple space-y-1">
                    <li>• Descrição otimizada da vaga</li>
                    <li>• Lista de requisitos relevantes</li>
                    <li>• Benefícios atrativos para o mercado</li>
                    <li>• Faixa salarial baseada no mercado</li>
                    <li>• Análise de competitividade</li>
                  </ul>
                </div>

                <div className="flex justify-end gap-2">
                  <Button variant="outline" onClick={() => setShowAIGenerator(false)}>
                    Cancelar
                  </Button>
                  <Button className="gap-2 bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    Gerar Template
                  </Button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
