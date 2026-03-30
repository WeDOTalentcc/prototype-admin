"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { textStyles } from "@/lib/design-tokens"
import {
  BarChart3,
  BookOpen,
  Brain,
  Building,
  CheckCircle,
  Code,
  Eye,
  Gauge,
  Globe,
  History,
  Library,
  Pencil,
  Plus,
  RefreshCw,
  Star,
  Target,
  Timer,
  TrendingUp,
  Trophy,
  UserCheck,
  Users,
  X,
} from "lucide-react"

interface TestLibraryModalProps {
  open: boolean
  onClose: () => void
  onTestPreview: () => void
  onTestHistoryOpen: (testName: string) => void
}

export function TestLibraryModal({ open, onClose, onTestPreview, onTestHistoryOpen }: TestLibraryModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-white dark:bg-lia-bg-primary rounded-md w-full max-w-6xl max-h-[90vh] overflow-hidden animate-fadeIn">
        {/* Header */}
        <div className="bg-wedo-purple p-5 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-lia-bg-primary/20 rounded-md">
                <Library className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Biblioteca de Testes da LIA</h2>
                <p className="text-wedo-purple text-sm">Testes validados e organizados por área de atuação</p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-lia-bg-primary/20 rounded-md transition-colors motion-reduce:transition-none"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Conteúdo */}
        <div className="flex h-[calc(90vh-100px)]">
          {/* Sidebar de Categorias */}
          <div className="w-64 bg-gray-50 dark:bg-lia-bg-secondary p-4 border-r border-lia-border-subtle dark:border-lia-border-subtle overflow-y-auto">
            <h3 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary uppercase mb-3">Categorias</h3>
            <div className="space-y-1">
              {[
                { icon: <Code className="w-4 h-4" />, label: 'Desenvolvimento', count: 24, color: 'text-lia-text-primary dark:text-lia-text-primary' },
                { icon: <Pencil className="w-4 h-4" />, label: 'Design & UX', count: 18, color: 'text-lia-text-primary dark:text-lia-text-primary', active: true },
                { icon: <BarChart3 className="w-4 h-4" />, label: 'Dados & Analytics', count: 15, color: 'text-lia-text-primary dark:text-lia-text-primary' },
                { icon: <Users className="w-4 h-4" />, label: 'Gestão & Liderança', count: 12, color: 'text-lia-text-primary dark:text-lia-text-primary' },
                { icon: <Target className="w-4 h-4" />, label: 'Marketing & Vendas', count: 20, color: 'text-lia-text-primary dark:text-lia-text-primary' },
                { icon: <Building className="w-4 h-4" />, label: 'Administrativo', count: 10, color: 'text-lia-text-secondary dark:text-lia-text-tertiary' },
                { icon: <Globe className="w-4 h-4" />, label: 'Idiomas', count: 8, color: 'text-lia-text-primary dark:text-lia-text-primary' },
                { icon: <Brain className="w-4 h-4 text-wedo-cyan" />, label: 'Soft Skills', count: 14, color: 'text-lia-text-primary dark:text-lia-text-primary' }
              ].map((category) => (
                <button
                  key={category.label}
                  className={`w-full flex items-center justify-between p-2.5 rounded-md transition-colors motion-reduce:transition-none ${
                    category.active
                      ? 'bg-white dark:bg-lia-bg-primary border border-lia-border-default dark:border-lia-border-subtle'
                      : 'hover:bg-lia-bg-primary dark:hover:bg-gray-900'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <span className={category.color}>{category.icon}</span>
                    <span className="text-sm font-medium text-lia-text-primary dark:text-lia-text-primary">{category.label}</span>
                  </div>
                  <Badge className="bg-gray-100 dark:bg-lia-bg-elevated text-lia-text-secondary dark:text-lia-text-secondary text-xs">
                    {category.count}
                  </Badge>
                </button>
              ))}
            </div>

            <div className="mt-6 pt-6 border-t border-lia-border-subtle dark:border-lia-border-subtle">
              <h3 className="text-xs font-semibold text-lia-text-primary dark:text-lia-text-primary uppercase mb-3">Filtros</h3>
              <div className="space-y-3">
                <div>
                  <label className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">Nível</label>
                  <select className="w-full mt-1 p-2 text-sm border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-primary">
                    <option>Todos</option>
                    <option>Júnior</option>
                    <option>Pleno</option>
                    <option>Sênior</option>
                  </select>
                </div>
                <div>
                  <label className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">Duração</label>
                  <select className="w-full mt-1 p-2 text-sm border border-lia-border-subtle dark:border-lia-border-default rounded-md bg-white dark:bg-lia-bg-primary">
                    <option>Qualquer</option>
                    <option>5-10 min</option>
                    <option>10-20 min</option>
                    <option>20-30 min</option>
                    <option>30+ min</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Lista de Testes */}
          <div className="flex-1 p-6 overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-lia-text-primary dark:text-lia-text-primary mb-1">
                Testes de Design & UX
              </h3>
              <p className="text-sm text-lia-text-secondary dark:text-lia-text-tertiary">
                18 testes disponíveis • Média de 85% de aprovação
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Teste 1 */}
              <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 dark:hover:border-gray-500 transition-colors motion-reduce:transition-none">
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                        UX Design - Fundamentos
                      </h4>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Teste básico de conceitos e heurísticas de UX
                      </p>
                    </div>
                    <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-lia-text-disabled text-xs">Popular</Badge>
                  </div>

                  {/* Mini Dashboard de Indicadores */}
                  <div className="bg-gray-50 dark:bg-lia-bg-primary rounded-md p-3 mb-3">
                    {/* Nota Média em Destaque */}
                    <div className="flex items-center justify-between mb-3 pb-3 border-b border-lia-border-subtle dark:border-lia-border-subtle">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-wedo-purple/15 dark:bg-wedo-purple/30 rounded-md">
                          <Trophy className="w-5 h-5 text-lia-text-primary dark:text-lia-text-primary" />
                        </div>
                        <div>
                          <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">Nota Média Geral</p>
                          <div className="flex items-baseline gap-2">
                            <p className="text-2xl font-bold text-lia-text-primary dark:text-lia-text-primary">7.4</p>
                            <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">/10</span>
                            <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-lia-text-disabled text-xs">
                              <TrendingUp className="w-2.5 h-2.5 mr-0.5" />
                              +0.3
                            </Badge>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className={textStyles.description}>Baseado em</p>
                        <p className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary">2.5k testes</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-gray-200 dark:bg-lia-bg-secondary/30 rounded-md">
                          <Target className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                        </div>
                        <div>
                          <p className={textStyles.description}>Taxa Sucesso</p>
                          <p className="text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">78%</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-gray-200 dark:bg-lia-bg-secondary/30 rounded-md">
                          <Gauge className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                        </div>
                        <div>
                          <p className={textStyles.description}>Dificuldade Real</p>
                          <p className="text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">Médio+</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-gray-200 dark:bg-lia-bg-secondary/30 rounded-md">
                          <UserCheck className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                        </div>
                        <div>
                          <p className={textStyles.description}>Conclusão</p>
                          <p className="text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">92%</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-gray-200 dark:bg-lia-bg-secondary/30 rounded-md">
                          <Timer className="w-3.5 h-3.5 text-lia-text-primary dark:text-lia-text-primary" />
                        </div>
                        <div>
                          <p className={textStyles.description}>Tempo Médio</p>
                          <p className="text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">13min</p>
                        </div>
                      </div>
                    </div>

                    {/* Barra de Distribuição de Notas */}
                    <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                      <p className={`${textStyles.description} mb-2`}>Distribuição de Notas</p>
                      <div className="flex items-end gap-1 h-8">
                        <div className="flex-1 bg-status-error rounded-t" style={{height: '20%'}} title="0-40%: 5%"></div>
                        <div className="flex-1 bg-gray-600 rounded-t" style={{height: '30%'}} title="40-60%: 15%"></div>
                        <div className="flex-1 bg-gray-600 dark:bg-lia-bg-elevated rounded-t" style={{height: '60%'}} title="60-80%: 35%"></div>
                        <div className="flex-1 bg-gray-700 rounded-t" style={{height: '80%'}} title="80-100%: 45%"></div>
                      </div>
                      <div className="flex justify-between mt-1">
                        <span className={textStyles.bodySmall}>0%</span>
                        <span className={textStyles.bodySmall}>100%</span>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Questões:</span>
                      <span className="font-medium">5 perguntas</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Tempo total:</span>
                      <span className="font-medium">15 minutos</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Nível:</span>
                      <Badge className="bg-gray-200 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs">Pleno</Badge>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="flex -space-x-1">
                          <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center">
                            <CheckCircle className="w-3 h-3 text-white" />
                          </div>
                        </div>
                        <span className={textStyles.description}>2.5k usos</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-lia-text-secondary fill-gray-400 dark:text-lia-text-tertiary dark:fill-gray-500" />
                        <span className="text-xs font-medium">4.8</span>
                      </div>
                    </div>
                    <div className="flex gap-1.5">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={onTestPreview}
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        Ver
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={() => onTestHistoryOpen('UX Design - Fundamentos')}
                      >
                        <History className="w-3 h-3 mr-1" />
                        Histórico
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200 text-white"
                        onClick={onClose}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        Usar
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Teste 2 */}
              <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 dark:hover:border-gray-500 transition-colors motion-reduce:transition-none">
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                        Design System & Componentes
                      </h4>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Avaliação sobre criação e manutenção de DS
                      </p>
                    </div>
                    <Badge className="bg-gray-200 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs">Novo</Badge>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Questões:</span>
                      <span className="font-medium">7 perguntas</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Tempo total:</span>
                      <span className="font-medium">20 minutos</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Nível:</span>
                      <Badge className="bg-gray-300 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs">Sênior</Badge>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="flex -space-x-1">
                          <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center">
                            <CheckCircle className="w-3 h-3 text-white" />
                          </div>
                        </div>
                        <span className={textStyles.description}>850 usos</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-lia-text-secondary fill-gray-400 dark:text-lia-text-tertiary dark:fill-gray-500" />
                        <span className="text-xs font-medium">4.9</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={onTestPreview}
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        Visualizar
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200 text-white"
                        onClick={onClose}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        Usar Este
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Teste 3 */}
              <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 dark:hover:border-gray-500 transition-colors motion-reduce:transition-none">
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                        Pesquisa com Usuários
                      </h4>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Métodos de pesquisa e análise de dados
                      </p>
                    </div>
                    <Badge className="bg-gray-200 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs">Recomendado</Badge>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Questões:</span>
                      <span className="font-medium">6 perguntas</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Tempo total:</span>
                      <span className="font-medium">18 minutos</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Nível:</span>
                      <Badge className="bg-gray-200 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs">Pleno</Badge>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="flex -space-x-1">
                          <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center">
                            <CheckCircle className="w-3 h-3 text-white" />
                          </div>
                        </div>
                        <span className={textStyles.description}>1.2k usos</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-lia-text-secondary fill-gray-400 dark:text-lia-text-tertiary dark:fill-gray-500" />
                        <span className="text-xs font-medium">4.7</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={onTestPreview}
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        Visualizar
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200 text-white"
                        onClick={onClose}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        Usar Este
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Teste 4 */}
              <div className="bg-white dark:bg-lia-bg-secondary rounded-md border border-lia-border-subtle dark:border-lia-border-subtle hover:border-gray-400 dark:hover:border-gray-500 transition-colors motion-reduce:transition-none">
                <div className="p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary mb-1">
                        Prototipagem e Ferramentas
                      </h4>
                      <p className="text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                        Figma, Sketch, Adobe XD e prototipagem
                      </p>
                    </div>
                    <Badge className="bg-gray-100 text-lia-text-primary dark:text-lia-text-primary text-xs">Técnico</Badge>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Questões:</span>
                      <span className="font-medium">4 perguntas</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Tempo total:</span>
                      <span className="font-medium">12 minutos</span>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-lia-text-primary dark:text-lia-text-primary">Nível:</span>
                      <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-lia-text-disabled text-xs">Júnior</Badge>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="flex -space-x-1">
                          <div className="w-5 h-5 rounded-full bg-gray-700 flex items-center justify-center">
                            <CheckCircle className="w-3 h-3 text-white" />
                          </div>
                        </div>
                        <span className={textStyles.description}>3.1k usos</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3 h-3 text-lia-text-secondary fill-gray-400 dark:text-lia-text-tertiary dark:fill-gray-500" />
                        <span className="text-xs font-medium">4.6</span>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={onTestPreview}
                      >
                        <Eye className="w-3 h-3 mr-1" />
                        Visualizar
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 text-xs bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200 text-white"
                        onClick={onClose}
                      >
                        <RefreshCw className="w-3 h-3 mr-1" />
                        Usar Este
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Botão para carregar mais */}
            <div className="mt-6 text-center">
              <Button variant="outline">
                <Plus className="w-4 h-4 mr-2" />
                Carregar Mais Testes
              </Button>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle p-4 bg-gray-50 dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-xs text-lia-text-primary dark:text-lia-text-primary">
              <span className="flex items-center gap-1">
                <BookOpen className="w-3 h-3" />
                121 testes disponíveis
              </span>
              <span className="flex items-center gap-1">
                <Users className="w-3 h-3" />
                Usado por 5.2k empresas
              </span>
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                87% taxa de sucesso
              </span>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                Fechar
              </Button>
              <Button className="bg-gray-900 hover:bg-gray-800 dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200 text-white">
                <Plus className="w-4 h-4 mr-2" />
                Criar Novo Teste
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
