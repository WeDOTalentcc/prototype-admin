"use client"

import React, { use, useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  FileCode,
  Brain,
  Clock,
  BarChart3,
  Plus,
  Search,
  Settings,
  Filter,
  Code2,
  Calculator,
  FileSpreadsheet,
  Users,
  MoreHorizontal,
  CheckCircle2,
  AlertCircle,
  Archive,
  Pencil,
  Target,
  TrendingUp,
  Timer,
  Percent,
  Loader2,
  RefreshCw
} from "lucide-react"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { useTechnicalTests, ClientTest } from "@/hooks/admin/useTechnicalTests"
import { toast } from "sonner"

type TestCategory = 'coding' | 'logic' | 'domain' | 'personality'
type TestStatus = 'active' | 'draft' | 'archived'
type TestDifficulty = 'easy' | 'medium' | 'hard'

interface DisplayTest {
  id: string
  testId: string
  name: string
  category: TestCategory
  subcategory?: string
  duration: number
  difficulty: TestDifficulty
  status: TestStatus
  enabled: boolean
  passingScore: number
  testsTaken: number
  avgScore: number
  completionRate: number
  lastUsed?: string
}

const categoryConfig: Record<TestCategory, { label: string, icon: React.ComponentType<{ className?: string }>, color: string, bgColor: string }> = {
  coding: { label: 'Coding', icon: Code2, color: 'text-gray-600 dark:text-gray-400', bgColor: 'bg-gray-100 dark:bg-gray-800' },
  logic: { label: 'Lógica/Raciocínio', icon: Brain, color: 'text-wedo-purple', bgColor: 'bg-wedo-purple/15 dark:bg-wedo-purple/30' },
  domain: { label: 'Específico', icon: FileSpreadsheet, color: 'text-status-warning', bgColor: 'bg-status-warning/15 dark:bg-status-warning/30' },
  personality: { label: 'Personalidade/Cultura', icon: Users, color: 'text-status-success', bgColor: 'bg-status-success/15 dark:bg-status-success/30' }
}

const statusConfig: Record<TestStatus, { label: string, variant: 'success' | 'warning' | 'default' }> = {
  active: { label: 'Ativo', variant: 'success' },
  draft: { label: 'Rascunho', variant: 'warning' },
  archived: { label: 'Arquivado', variant: 'default' }
}

const difficultyConfig: Record<TestDifficulty, { label: string, color: string }> = {
  easy: { label: 'Fácil', color: 'text-status-success bg-status-success/15 dark:bg-status-success/30' },
  medium: { label: 'Médio', color: 'text-status-warning bg-status-warning/15 dark:bg-status-warning/30' },
  hard: { label: 'Difícil', color: 'text-status-error bg-status-error/15 dark:bg-status-error/30' }
}

function mapClientTestToDisplay(clientTest: ClientTest): DisplayTest {
  return {
    id: clientTest.id,
    testId: clientTest.testId,
    name: clientTest.test?.name || 'Unknown Test',
    category: (clientTest.test?.category as TestCategory) || 'coding',
    subcategory: clientTest.test?.subcategory,
    duration: clientTest.customDuration || clientTest.test?.duration || 0,
    difficulty: (clientTest.test?.difficulty as TestDifficulty) || 'medium',
    status: (clientTest.test?.status as TestStatus) || 'active',
    enabled: clientTest.enabled,
    passingScore: clientTest.customPassingScore || clientTest.test?.passingScore || 0,
    testsTaken: clientTest.testsTaken,
    avgScore: clientTest.avgScore,
    completionRate: clientTest.completionRate,
    lastUsed: clientTest.lastUsed,
  }
}

export default function ClientTestesPage({
  params
}: {
  params: Promise<{ clientId: string }>
}) {
  const { clientId } = use(params)
  const { 
    tests: clientTests, 
    stats, 
    isLoading, 
    isUpdating, 
    error, 
    refetch, 
    toggleTestEnabled,
    seedTests 
  } = useTechnicalTests(clientId)
  
  const [searchQuery, setSearchQuery] = useState('')
  const [categoryFilter, setCategoryFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [activeTab, setActiveTab] = useState<string>('all')
  const [togglingTests, setTogglingTests] = useState<Set<string>>(new Set())

  const tests: DisplayTest[] = clientTests.map(mapClientTestToDisplay)

  const handleToggleTest = async (testId: string) => {
    const test = tests.find(t => t.testId === testId)
    if (!test) return

    setTogglingTests(prev => new Set(prev).add(testId))
    const success = await toggleTestEnabled(testId, !test.enabled)
    setTogglingTests(prev => {
      const next = new Set(prev)
      next.delete(testId)
      return next
    })

    if (success) {
      toast.success(test.enabled ? 'Teste desabilitado' : 'Teste habilitado')
    } else {
      toast.error('Erro ao atualizar teste')
    }
  }

  const handleSeedTests = async () => {
    const success = await seedTests()
    if (success) {
      toast.success('Testes inicializados com sucesso')
    } else {
      toast.error('Erro ao inicializar testes')
    }
  }

  const filteredTests = tests.filter(test => {
    const matchesSearch = test.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         (test.subcategory?.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesCategory = categoryFilter === 'all' || test.category === categoryFilter
    const matchesStatus = statusFilter === 'all' || test.status === statusFilter
    const matchesTab = activeTab === 'all' || test.category === activeTab
    return matchesSearch && matchesCategory && matchesStatus && matchesTab
  })

  const totalTests = stats?.totalTests ?? tests.length
  const activeTests = stats?.activeTests ?? tests.filter(t => t.status === 'active').length
  const enabledTests = stats?.enabledTests ?? tests.filter(t => t.enabled).length
  const totalTestsTaken = stats?.totalTestsTaken ?? tests.reduce((acc, t) => acc + t.testsTaken, 0)
  const avgCompletionRate = stats?.avgCompletionRate ?? (
    tests.filter(t => t.testsTaken > 0).reduce((acc, t) => acc + t.completionRate, 0) / 
    (tests.filter(t => t.testsTaken > 0).length || 1)
  )
  const testsTakenThisWeek = stats?.testsTakenThisWeek ?? 0

  const codingTests = stats?.byCategory?.coding ?? { 
    total: tests.filter(t => t.category === 'coding').length, 
    enabled: tests.filter(t => t.category === 'coding' && t.enabled).length 
  }
  const logicTests = stats?.byCategory?.logic ?? { 
    total: tests.filter(t => t.category === 'logic').length, 
    enabled: tests.filter(t => t.category === 'logic' && t.enabled).length 
  }
  const domainTests = stats?.byCategory?.domain ?? { 
    total: tests.filter(t => t.category === 'domain').length, 
    enabled: tests.filter(t => t.category === 'domain' && t.enabled).length 
  }
  const personalityTests = stats?.byCategory?.personality ?? { 
    total: tests.filter(t => t.category === 'personality').length, 
    enabled: tests.filter(t => t.category === 'personality' && t.enabled).length 
  }

  const formatDate = (dateStr: string | undefined) => {
    if (!dateStr) return 'Nunca'
    try {
      return new Date(dateStr).toLocaleDateString('pt-BR', {
        day: '2-digit',
        month: 'short'
      })
    } catch {
      return dateStr
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-600 dark:text-gray-400" />
          <p className="text-sm text-gray-400 dark:text-gray-500">
            Carregando testes técnicos...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 mx-auto mb-4 text-status-error" />
          <p className="text-sm mb-4 text-gray-400 dark:text-gray-500">
            Erro ao carregar testes técnicos
          </p>
          <Button onClick={refetch} variant="outline" size="sm">
            <RefreshCw className="w-4 h-4 mr-2" />
            Tentar novamente
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <FileCode className="w-6 h-6 text-gray-600 dark:text-gray-400" />
            <h2 
              className="text-lg font-semibold text-gray-800 dark:text-gray-100"
            >
              Testes Técnicos
            </h2>
          </div>
          <p className="text-sm text-gray-400 dark:text-gray-500">
            Biblioteca de testes e avaliações técnicas para este cliente
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={refetch} disabled={isUpdating}>
            <RefreshCw className={`w-4 h-4 mr-2 ${isUpdating ? 'animate-spin' : ''}`} />
            Atualizar
          </Button>
          <Button variant="outline" size="sm">
            <Settings className="w-4 h-4 mr-2" />
            Configurações
          </Button>
          <Button 
            size="sm"
            className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            <Plus className="w-4 h-4 mr-2" />
            Adicionar Teste
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 dark:text-gray-500">
                  Total de Testes
                </p>
                <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100">
                  {totalTests}
                </p>
              </div>
              <div className="w-10 h-10 rounded-md bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
                <FileCode className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              </div>
            </div>
            <p className="text-xs mt-2 text-gray-400 dark:text-gray-500">
              {enabledTests} habilitados para uso
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 dark:text-gray-500">
                  Testes Realizados
                </p>
                <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100">
                  {totalTestsTaken.toLocaleString()}
                </p>
              </div>
              <div className="w-10 h-10 rounded-md bg-wedo-purple/10 dark:bg-wedo-purple/20 flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-wedo-purple" />
              </div>
            </div>
            <div className="flex items-center gap-1 mt-2">
              <TrendingUp className="w-3 h-3 text-status-success" />
              <span className="text-xs text-status-success">+{testsTakenThisWeek} esta semana</span>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 dark:text-gray-500">
                  Taxa de Conclusão
                </p>
                <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100">
                  {avgCompletionRate.toFixed(0)}%
                </p>
              </div>
              <div className="w-10 h-10 rounded-md bg-status-success/10 dark:bg-status-success/20 flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-status-success" />
              </div>
            </div>
            <p className="text-xs mt-2 text-gray-400 dark:text-gray-500">
              Média geral de conclusão
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400 dark:text-gray-500">
                  Testes Ativos
                </p>
                <p className="text-2xl font-semibold mt-1 text-gray-800 dark:text-gray-100">
                  {activeTests}
                </p>
              </div>
 <div className="w-10 h-10 rounded-md bg-gray-50 dark:bg-gray-800 flex items-center justify-center">
                <Target className="w-5 h-5 text-gray-900 dark:text-gray-50" />
              </div>
            </div>
            <p className="text-xs mt-2 text-gray-400 dark:text-gray-500">
              {stats?.draftTests ?? tests.filter(t => t.status === 'draft').length} em rascunho
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="border-l-4 border-l-gray-400 dark:border-l-gray-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Code2 className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100">Coding</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {codingTests.total} testes ({codingTests.enabled} ativos)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-purple-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Brain className="w-5 h-5 text-wedo-purple" />
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100">Lógica</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {logicTests.total} testes ({logicTests.enabled} ativos)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-amber-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="w-5 h-5 text-status-warning" />
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100">Específico</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {domainTests.total} testes ({domainTests.enabled} ativos)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="border-l-4 border-l-emerald-500">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <Users className="w-5 h-5 text-status-success" />
              <div>
                <p className="text-sm font-medium text-gray-800 dark:text-gray-100">Personalidade</p>
                <p className="text-xs text-gray-400 dark:text-gray-500">
                  {personalityTests.total} testes ({personalityTests.enabled} ativos)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <CardTitle className="text-base text-gray-800 dark:text-gray-100">
              Biblioteca de Testes
            </CardTitle>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                  <SelectTrigger className="w-[150px] h-9">
                    <SelectValue placeholder="Categoria" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todas Categorias</SelectItem>
                    <SelectItem value="coding">Coding</SelectItem>
                    <SelectItem value="logic">Lógica</SelectItem>
                    <SelectItem value="domain">Específico</SelectItem>
                    <SelectItem value="personality">Personalidade</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                  <SelectTrigger className="w-[130px] h-9">
                    <SelectValue placeholder="Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">Todos Status</SelectItem>
                    <SelectItem value="active">Ativo</SelectItem>
                    <SelectItem value="draft">Rascunho</SelectItem>
                    <SelectItem value="archived">Arquivado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Buscar teste..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 h-9"
                />
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="mb-4">
              <TabsTrigger value="all">Todos</TabsTrigger>
              <TabsTrigger value="coding" className="flex items-center gap-1">
                <Code2 className="w-3 h-3" />
                Coding
              </TabsTrigger>
              <TabsTrigger value="logic" className="flex items-center gap-1">
                <Brain className="w-3 h-3 text-wedo-cyan" />
                Lógica
              </TabsTrigger>
              <TabsTrigger value="domain" className="flex items-center gap-1">
                <FileSpreadsheet className="w-3 h-3" />
                Específico
              </TabsTrigger>
              <TabsTrigger value="personality" className="flex items-center gap-1">
                <Users className="w-3 h-3" />
                Personalidade
              </TabsTrigger>
            </TabsList>

            <div className="space-y-2">
              {filteredTests.length === 0 ? (
                <div className="text-center py-8">
                  <FileCode className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-sm mb-4 text-gray-400 dark:text-gray-500">
                    {tests.length === 0 
                      ? 'Nenhum teste configurado para este cliente'
                      : 'Nenhum teste encontrado com os filtros aplicados'
                    }
                  </p>
                  {tests.length === 0 && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={handleSeedTests}
                      disabled={isUpdating}
                    >
                      {isUpdating ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Plus className="w-4 h-4 mr-2" />
                      )}
                      Inicializar testes padrão
                    </Button>
                  )}
                </div>
              ) : (
                filteredTests.map((test) => {
                  const category = categoryConfig[test.category]
                  const status = statusConfig[test.status]
                  const difficulty = difficultyConfig[test.difficulty]
                  const CategoryIcon = category.icon
                  const isToggling = togglingTests.has(test.testId)

                  return (
                    <div 
                      key={test.id}
                      className={`flex items-center gap-4 p-4 rounded-md border hover:border-gray-900 dark:hover:border-gray-50 transition-colors ${
                        !test.enabled ? 'opacity-60' : ''
                      }`}
                      className="border-gray-200 dark:border-gray-700"
                    >
                      <div className={`w-10 h-10 rounded-md ${category.bgColor} flex items-center justify-center shrink-0`}>
                        <CategoryIcon className={`w-5 h-5 ${category.color}`} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p 
                            className="font-medium truncate text-gray-800 dark:text-gray-100"
                          >
                            {test.name}
                          </p>
                          {test.subcategory && (
                            <Badge variant="outline" className="text-xs">
                              {test.subcategory}
                            </Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs text-gray-400 dark:text-gray-500">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {test.duration} min
                          </span>
                          <span className={`px-1.5 py-0.5 rounded ${difficulty.color}`}>
                            {difficulty.label}
                          </span>
                          {test.passingScore > 0 && (
                            <span className="flex items-center gap-1">
                              <Target className="w-3 h-3" />
                              Mín: {test.passingScore}%
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-6">
                        <div className="text-center min-w-[70px]">
                          <p className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                            {test.testsTaken}
                          </p>
                          <p className="text-xs text-gray-400 dark:text-gray-500">
                            realizados
                          </p>
                        </div>

                        {test.testsTaken > 0 && (
                          <>
                            <div className="text-center min-w-[60px]">
                              <p className="text-lg font-semibold text-gray-800 dark:text-gray-100">
                                {test.avgScore > 0 ? `${test.avgScore}%` : '-'}
                              </p>
                              <p className="text-xs text-gray-400 dark:text-gray-500">
                                média
                              </p>
                            </div>
                            <div className="text-center min-w-[60px]">
                              <p className="text-lg font-semibold text-status-success">
                                {test.completionRate}%
                              </p>
                              <p className="text-xs text-gray-400 dark:text-gray-500">
                                conclusão
                              </p>
                            </div>
                          </>
                        )}

                        <Badge variant={status.variant}>
                          {status.label}
                        </Badge>

                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 dark:text-gray-500">
                            {test.enabled ? 'Habilitado' : 'Desabilitado'}
                          </span>
                          {isToggling ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <Switch
                              checked={test.enabled}
                              onCheckedChange={() => handleToggleTest(test.testId)}
                              disabled={test.status === 'archived' || isUpdating}
                            />
                          )}
                        </div>

                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="w-4 h-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Pencil className="w-4 h-4 mr-2" />
                              Editar Configuração
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Timer className="w-4 h-4 mr-2" />
                              Ajustar Tempo
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Percent className="w-4 h-4 mr-2" />
                              Nota de Corte
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <BarChart3 className="w-4 h-4 mr-2" />
                              Ver Estatísticas
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            {test.status !== 'archived' ? (
                              <DropdownMenuItem>
                                <Archive className="w-4 h-4 mr-2" />
                                Arquivar
                              </DropdownMenuItem>
                            ) : (
                              <DropdownMenuItem>
                                <CheckCircle2 className="w-4 h-4 mr-2" />
                                Reativar
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>
                  )
                })
              )}
            </div>
          </Tabs>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-gray-800 dark:text-gray-100">
              Testes Mais Utilizados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {tests
                .filter(t => t.testsTaken > 0)
                .sort((a, b) => b.testsTaken - a.testsTaken)
                .slice(0, 5)
                .map((test, index) => {
                  const category = categoryConfig[test.category]
                  const CategoryIcon = category.icon
                  return (
                    <div 
                      key={test.id}
                      className="flex items-center gap-3 p-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800/50"
                    >
                      <span 
                        className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center text-xs font-medium text-gray-400 dark:text-gray-500"
                      >
                        {index + 1}
                      </span>
                      <div className={`w-8 h-8 rounded-md ${category.bgColor} flex items-center justify-center`}>
                        <CategoryIcon className={`w-4 h-4 ${category.color}`} />
                      </div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-800 dark:text-gray-100">
                          {test.name}
                        </p>
                        <p className="text-xs text-gray-400 dark:text-gray-500">
                          Último uso: {formatDate(test.lastUsed)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-semibold text-gray-800 dark:text-gray-100">
                          {test.testsTaken}
                        </p>
                        <p className="text-xs text-gray-400 dark:text-gray-500">
                          aplicações
                        </p>
                      </div>
                    </div>
                  )
                })}
              {tests.filter(t => t.testsTaken > 0).length === 0 && (
                <p className="text-center text-sm py-4 text-gray-400 dark:text-gray-500">
                  Nenhum teste realizado ainda
                </p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base text-gray-800 dark:text-gray-100">
              Desempenho por Categoria
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(categoryConfig).map(([key, config]) => {
                const categoryTests = tests.filter(t => t.category === key && t.testsTaken > 0)
                const avgScore = categoryTests.length > 0
                  ? categoryTests.reduce((acc, t) => acc + t.avgScore, 0) / categoryTests.length
                  : 0
                const avgCompletion = categoryTests.length > 0
                  ? categoryTests.reduce((acc, t) => acc + t.completionRate, 0) / categoryTests.length
                  : 0
                const Icon = config.icon

                return (
                  <div key={key} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded-md ${config.bgColor} flex items-center justify-center`}>
                          <Icon className={`w-4 h-4 ${config.color}`} />
                        </div>
                        <span className="text-sm font-medium text-gray-800 dark:text-gray-100">
                          {config.label}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        {avgScore > 0 && (
                          <span className="text-gray-400 dark:text-gray-500">
                            Média: <span className="font-medium text-gray-800 dark:text-gray-100">{avgScore.toFixed(0)}%</span>
                          </span>
                        )}
                        <span className="text-gray-400 dark:text-gray-500">
                          Conclusão: <span className="font-medium text-status-success">{avgCompletion.toFixed(0)}%</span>
                        </span>
                      </div>
                    </div>
                    <div className="w-full h-2 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gray-900 dark:bg-gray-50 rounded-full transition-all"
                        style={{width: `${avgCompletion}%`}}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
