"use client"

import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { textStyles } from "@/lib/design-tokens"
import {
  Award,
  BarChart3,
  Brain,
  Calendar,
  Clock,
  Download,
  Gauge,
  History,
  Target,
  Timer,
  TrendingUp,
  Trophy,
  UserCheck,
  Users,
  X,
  XCircle,
} from "lucide-react"

interface TestHistoryModalProps {
  open: boolean
  onClose: () => void
  testName: string | null
}

export function TestHistoryModal({ open, onClose, testName }: TestHistoryModalProps) {
  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div className="bg-white dark:bg-lia-bg-primary rounded-md w-full max-w-5xl max-h-[90vh] overflow-hidden animate-fadeIn">
        {/* Header */}
        <div className="bg-gray-900 dark:bg-lia-bg-secondary p-5 text-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-lia-bg-primary/20 rounded-md">
                <History className="w-5 h-5" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Histórico de Uso do Teste</h2>
                <p className="text-lia-text-disabled text-sm">{testName || 'UX Design - Fundamentos'}</p>
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

        {/* Estatísticas Gerais */}
        <div className="p-6 border-b border-lia-border-subtle dark:border-lia-border-subtle bg-gray-50 dark:bg-lia-bg-secondary">
          {/* Nota Média Destacada */}
          <div className="bg-wedo-purple rounded-md p-4 mb-4 text-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-lia-bg-primary/20 rounded-md">
                  <Trophy className="w-6 h-6" />
                </div>
                <div>
                  <p className="text-sm opacity-90">Nota Média Histórica</p>
                  <div className="flex items-baseline gap-3">
                    <p className="text-base-ui font-semibold">7.4</p>
                    <span className="text-lg opacity-80">/10</span>
                    <div className="flex items-center gap-2 ml-3">
                      <Badge className="bg-lia-bg-primary/20 text-white border-white/30">
                        <TrendingUp className="w-3 h-3 mr-1" />
                        +0.3 vs mês anterior
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>

              {/* Mini gráfico de evolução */}
              <div className="bg-lia-bg-primary/10 rounded-md p-3">
                <p className="text-xs opacity-80 mb-2">Evolução (6 meses)</p>
                <div className="flex items-end gap-1 h-10">
                  {[6.8, 7.0, 7.1, 7.2, 7.1, 7.4].map((value, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-lia-bg-primary/30 rounded-t hover:bg-lia-bg-primary/40 transition-colors motion-reduce:transition-none relative group"
                      style={{height: `${((value - 6) / 2) * 100}%`}}
                    >
                      <span className="absolute -top-5 left-1/2 -translate-x-1/2 text-xs opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                        {value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-5 gap-4">
            <div className="bg-white dark:bg-lia-bg-primary rounded-md p-4">
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-lia-text-primary dark:text-lia-text-primary" />
                <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">Total de Aplicações</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">2,547</p>
              <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mt-1">↑ 12% este mês</p>
            </div>

            <div className="bg-white dark:bg-lia-bg-primary rounded-md p-4">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-lia-text-primary dark:text-lia-text-primary" />
                <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">Taxa de Sucesso</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">78%</p>
              <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mt-1">Nota ≥ 7.0</p>
            </div>

            <div className="bg-white dark:bg-lia-bg-primary rounded-md p-4">
              <div className="flex items-center gap-2 mb-2">
                <UserCheck className="w-4 h-4 text-lia-text-primary dark:text-lia-text-primary" />
                <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">Taxa de Conclusão</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">92%</p>
              <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mt-1">Candidatos finalizam</p>
            </div>

            <div className="bg-white dark:bg-lia-bg-primary rounded-md p-4">
              <div className="flex items-center gap-2 mb-2">
                <Timer className="w-4 h-4 text-lia-text-primary dark:text-lia-text-primary" />
                <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">Tempo Médio</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">13min</p>
              <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mt-1">De 15min esperados</p>
            </div>

            <div className="bg-white dark:bg-lia-bg-primary rounded-md p-4">
              <div className="flex items-center gap-2 mb-2">
                <Gauge className="w-4 h-4 text-status-error" />
                <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">Dificuldade Percebida</span>
              </div>
              <p className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary">6.8/10</p>
              <p className="text-xs text-lia-text-primary dark:text-lia-text-primary mt-1">Médio-Alto</p>
            </div>
          </div>
        </div>

        {/* Lista de Vagas que Usaram */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-380px)]">
          <h3 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary mb-4">
            Vagas que Utilizaram Este Teste
          </h3>

          <div className="space-y-3">
            {/* Vaga 1 */}
            <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">UX Designer Sênior</h4>
                    <Badge className="bg-gray-900 text-white dark:bg-gray-200 dark:text-lia-text-disabled text-xs">Finalizada</Badge>
                    <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">Sodexo • São Paulo</span>
                  </div>
                  <div className="flex items-center gap-6 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Mar 2024
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      45 candidatos
                    </span>
                    <span className="flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      82% aprovação
                    </span>
                    <span className="flex items-center gap-1">
                      <Trophy className="w-3 h-3 text-lia-text-primary dark:text-lia-text-primary" />
                      3 contratados
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">Sucesso</p>
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">ROI: 320%</p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between mb-1">
                  <span className={textStyles.description}>Distribuição de Notas</span>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-gray-200 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs px-1.5">
                      <Trophy className="w-2.5 h-2.5 mr-0.5" />
                      Nota Média: 7.8/10
                    </Badge>
                  </div>
                </div>
                <div className="flex items-end gap-0.5 h-6">
                  {[2, 3, 5, 8, 12, 10, 5].map((height, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-gray-600 dark:bg-lia-bg-elevated rounded-t opacity-80"
                      style={{height: `${(height / 12) * 100}%`}}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Vaga 2 */}
            <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">Product Designer</h4>
                    <Badge className="bg-gray-200 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs">Em Andamento</Badge>
                    <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">Nubank • Remoto</span>
                  </div>
                  <div className="flex items-center gap-6 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Nov 2024
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      28 candidatos
                    </span>
                    <span className="flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      75% aprovação
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3 text-lia-text-primary dark:text-lia-text-primary" />
                      Em entrevistas
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-lia-text-primary dark:text-lia-text-primary">Ativo</p>
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">5 finalistas</p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between mb-1">
                  <span className={textStyles.description}>Distribuição de Notas</span>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-gray-200 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs px-1.5">
                      <Trophy className="w-2.5 h-2.5 mr-0.5" />
                      Nota Média: 7.2/10
                    </Badge>
                  </div>
                </div>
                <div className="flex items-end gap-0.5 h-6">
                  {[3, 4, 6, 7, 8, 4, 2].map((height, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-gray-600 dark:bg-lia-bg-elevated rounded-t opacity-80"
                      style={{height: `${(height / 8) * 100}%`}}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Vaga 3 */}
            <div className="bg-gray-50 dark:bg-lia-bg-secondary rounded-md p-4 border border-lia-border-subtle dark:border-lia-border-subtle">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h4 className="font-medium text-lia-text-primary dark:text-lia-text-primary">UI/UX Designer</h4>
                    <Badge className="bg-gray-100 text-lia-text-primary dark:text-lia-text-primary text-xs">Cancelada</Badge>
                    <span className="text-xs text-lia-text-primary dark:text-lia-text-primary">iFood • Campinas</span>
                  </div>
                  <div className="flex items-center gap-6 text-xs text-lia-text-secondary dark:text-lia-text-tertiary">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      Set 2024
                    </span>
                    <span className="flex items-center gap-1">
                      <Users className="w-3 h-3" />
                      18 candidatos
                    </span>
                    <span className="flex items-center gap-1">
                      <Target className="w-3 h-3" />
                      65% aprovação
                    </span>
                    <span className="flex items-center gap-1">
                      <XCircle className="w-3 h-3 text-lia-text-secondary" />
                      Vaga cancelada
                    </span>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-lia-text-secondary">Encerrada</p>
                  <p className="text-xs text-lia-text-primary dark:text-lia-text-primary">Sem contratação</p>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-lia-border-subtle dark:border-lia-border-subtle">
                <div className="flex items-center justify-between mb-1">
                  <span className={textStyles.description}>Distribuição de Notas</span>
                  <div className="flex items-center gap-2">
                    <Badge className="bg-gray-200 text-lia-text-primary dark:bg-lia-bg-elevated dark:text-lia-text-primary text-xs px-1.5">
                      <Trophy className="w-2.5 h-2.5 mr-0.5" />
                      Nota Média: 6.5/10
                    </Badge>
                  </div>
                </div>
                <div className="flex items-end gap-0.5 h-6">
                  {[4, 5, 6, 5, 3, 2, 1].map((height, i) => (
                    <div
                      key={i}
                      className="flex-1 bg-gray-400 rounded-t opacity-60"
                      style={{height: `${(height / 6) * 100}%`}}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Insights e Recomendações */}
          <div className="mt-6 bg-gray-100 dark:bg-lia-bg-secondary/20 rounded-md p-4 border border-lia-border-default dark:border-lia-border-subtle">
            <div className="flex items-start gap-3">
              <Brain className="w-5 h-5 text-wedo-cyan mt-0.5" />
              <div>
                <h4 className="text-sm font-semibold text-lia-text-primary dark:text-lia-text-primary mb-2">
                  Insights da LIA
                </h4>
                <ul className="space-y-1 text-xs text-lia-text-primary dark:text-lia-text-primary">
                  <li>• Este teste tem melhor performance com candidatos de nível Pleno e Sênior</li>
                  <li>• A questão 3 tem a menor taxa de acerto (45%) - considere revisar ou adicionar contexto</li>
                  <li>• Candidatos que pontuam acima de 75% têm 3x mais chance de serem contratados</li>
                  <li>• Tempo ideal de aplicação: Segunda a Quinta, entre 10h-12h ou 14h-17h</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t border-lia-border-subtle dark:border-lia-border-subtle p-4 bg-gray-50 dark:bg-lia-bg-secondary">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4 text-xs text-lia-text-primary dark:text-lia-text-primary">
              <span className="flex items-center gap-1">
                <TrendingUp className="w-3 h-3" />
                Performance acima da média
              </span>
              <span className="flex items-center gap-1">
                <Award className="w-3 h-3" />
                Top 10% dos testes mais eficazes
              </span>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" onClick={onClose}>
                Fechar
              </Button>
              <Button className="bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:hover:bg-gray-200 dark:text-lia-text-disabled">
                <Download className="w-4 h-4 mr-2" />
                Exportar Relatório
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
