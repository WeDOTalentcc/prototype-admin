"use client"

import { X, Code, Clock, Trophy, Users, CheckCircle, Loader2, AlertCircle, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

interface TechnicalTestModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: any
}

type TestStatus = 'pending' | 'in_progress' | 'completed'

const STATUS_CONFIG = {
  pending: {
    label: 'Pendente',
    icon: AlertCircle,
    color: 'var(--gray-400)',
    bgColor: 'rgba(156, 163, 175, 0.12)'
  },
  in_progress: {
    label: 'Em andamento',
    icon: Loader2,
    color: 'var(--status-warning)',
    bgColor: 'rgba(245, 158, 11, 0.12)'
  },
  completed: {
    label: 'Concluído',
    icon: CheckCircle,
    color: 'var(--status-success)',
    bgColor: 'rgba(16, 185, 129, 0.12)'
  }
}

export function TechnicalTestModal({ isOpen, onClose, candidate }: TechnicalTestModalProps) {
  if (!isOpen) return null

  const testData = candidate?.technicalTest ?? {
    status: 'completed',
    score: 78,
    duration: 72,
    maxDuration: 90,
    completedAt: '2024-01-15',
    categories: [
      { name: 'Design System', score: 95, avgScore: 72 },
      { name: 'Prototipagem', score: 90, avgScore: 68 },
      { name: 'User Research', score: 85, avgScore: 75 },
      { name: 'Ferramentas', score: 88, avgScore: 70 },
      { name: 'Metodologias Ágeis', score: 82, avgScore: 65 },
    ],
    averageScore: 72
  }

  const status: TestStatus = testData.status ?? 'pending'
  const statusConfig = STATUS_CONFIG[status]
  const StatusIcon = statusConfig.icon

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10B981'
    if (score >= 60) return '#6B7280'
    if (score >= 40) return '#F59E0B'
    return '#EF4444'
  }

  const getComparisonIcon = (candidateScore: number, avgScore: number) => {
    const diff = candidateScore - avgScore
    if (diff > 5) return <TrendingUp className="w-3 h-3" style={{ color: 'var(--status-success)' }} />
    if (diff < -5) return <TrendingDown className="w-3 h-3" style={{ color: 'var(--status-error)' }} />
    return <Minus className="w-3 h-3 text-gray-400" />
  }

  const getComparisonLabel = (candidateScore: number, avgScore: number) => {
    const diff = candidateScore - avgScore
    if (diff > 0) return `+${diff} acima da média`
    if (diff < 0) return `${diff} abaixo da média`
    return 'Na média'
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4" 
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.4)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div 
        className="w-full max-w-lg max-h-[85vh] overflow-hidden flex flex-col border border-gray-100" style={{ backgroundColor: 'var(--gray-50)', borderRadius: '10px', boxShadow: '0 16px 32px -8px rgba(0, 0, 0, 0.12)' }}
      >
        <div 
          className="flex items-center justify-between px-4 py-3 border-b border-b-gray-100"
        >
          <div className="flex items-center gap-2">
            <div 
              className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: 'rgba(96, 190, 209, 0.12)' }}
            >
              <Code className="w-4 h-4 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h2 
                className="text-base-ui font-semibold text-gray-950 dark:text-gray-50"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
              >
                Teste Técnico
              </h2>
              <p 
                className="text-xs text-gray-600"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
              >
                {candidate?.name ?? 'Candidato'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="h-7 w-7 p-0 flex items-center justify-center transition-colors hover:bg-gray-100 rounded-full text-gray-500"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4" style={{ backgroundColor: 'var(--gray-50)' }}>
          <div 
            className="flex items-center justify-between p-3 rounded-md mb-4"
            style={{ backgroundColor: statusConfig.bgColor, border: `1px solid ${statusConfig.color}30` }}
          >
            <div className="flex items-center gap-2">
              <StatusIcon 
                className={`w-4 h-4 ${status === 'in_progress' ? 'animate-spin' : ''}`} 
                style={{ color: statusConfig.color }} 
              />
              <span 
                className="text-xs font-medium"
                style={{ fontFamily: "'Open Sans', sans-serif", color: statusConfig.color }}
              >
                {statusConfig.label}
              </span>
            </div>
            {testData.completedAt && status === 'completed' && (
              <span 
                className="text-micro text-gray-600"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
              >
                Concluído em {new Date(testData.completedAt).toLocaleDateString('pt-BR')}
              </span>
            )}
          </div>

          {status === 'completed' && (
            <>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div 
                  className="p-3 rounded-md border border-gray-100"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Trophy className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    <span 
                      className="text-micro text-gray-600"
                      style={{ fontFamily: "'Open Sans', sans-serif" }}
                    >
                      Score Geral
                    </span>
                  </div>
                  <span 
                    className="text-2xl font-bold"
                    style={{ fontFamily: "'Open Sans', sans-serif", color: getScoreColor(testData.score) }}
                  >
                    {testData.score}
                  </span>
                  <span 
                    className="text-sm ml-1 text-gray-400"
                    style={{ fontFamily: "'Open Sans', sans-serif" }}
                  >
                    / 100
                  </span>
                </div>

                <div 
                  className="p-3 rounded-md border border-gray-100"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    <span 
                      className="text-micro text-gray-600"
                      style={{ fontFamily: "'Open Sans', sans-serif" }}
                    >
                      Tempo de Conclusão
                    </span>
                  </div>
                  <span 
                    className="text-2xl font-bold text-gray-950 dark:text-gray-50"
                    style={{ fontFamily: "'Open Sans', sans-serif" }}
                  >
                    {testData.duration}
                  </span>
                  <span 
                    className="text-sm ml-1 text-gray-400"
                    style={{ fontFamily: "'Open Sans', sans-serif" }}
                  >
                    / {testData.maxDuration} min
                  </span>
                </div>
              </div>

              <div 
                className="flex items-center gap-2 p-3 rounded-md mb-4"
                style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)', border: '1px solid rgba(96, 190, 209, 0.2)' }}
              >
                <Users className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                <span 
                  className="text-xs text-gray-600 dark:text-gray-400"
                  style={{ fontFamily: "'Open Sans', sans-serif" }}
                >
                  Comparação com outros candidatos:
                </span>
                <span 
                  className="text-xs font-semibold ml-auto"
                  style={{ 
                    fontFamily: "'Open Sans', sans-serif", 
                    color: testData.score >= testData.averageScore ? '#10B981' : '#EF4444' 
                  }}
                >
                  {getComparisonLabel(testData.score, testData.averageScore)}
                </span>
              </div>

              <div className="mb-4">
                <p 
                  className="text-xs font-semibold mb-3 text-gray-950 dark:text-gray-50"
                  style={{ fontFamily: "'Open Sans', sans-serif" }}
                >
                  Breakdown por Categoria
                </p>

                <div className="space-y-2.5">
                  {testData.categories?.map((category: any, index: number) => (
                    <div 
                      key={index}
                      className="p-3 rounded-md border border-gray-100"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span 
                          className="text-xs font-medium text-gray-950 dark:text-gray-50"
                          style={{ fontFamily: "'Open Sans', sans-serif" }}
                        >
                          {category.name}
                        </span>
                        <div className="flex items-center gap-2">
                          {getComparisonIcon(category.score, category.avgScore)}
                          <span 
                            className="text-xs font-bold"
                            style={{ fontFamily: "'Open Sans', sans-serif", color: getScoreColor(category.score) }}
                          >
                            {category.score}
                          </span>
                        </div>
                      </div>
                      <div className="relative">
                        <Progress 
                          value={category.score} 
                          className="h-1.5 bg-gray-200"
                        />
                        <div 
                          className="absolute top-0 h-1.5 rounded-full opacity-30 bg-gray-400" style={{ width: `${category.avgScore}%` }}
                        />
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span 
                          className="text-micro text-gray-600"
                          style={{ fontFamily: "'Open Sans', sans-serif" }}
                        >
                          Média dos candidatos: {category.avgScore}
                        </span>
                        <span 
                          className="text-micro"
                          style={{ 
                            fontFamily: "'Open Sans', sans-serif", 
                            color: category.score >= category.avgScore ? '#10B981' : '#EF4444' 
                          }}
                        >
                          {category.score >= category.avgScore ? '+' : ''}{category.score - category.avgScore}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}

          {status === 'pending' && (
            <div 
              className="flex flex-col items-center justify-center py-8 text-gray-400"
            >
              <AlertCircle className="w-12 h-12 mb-3" />
              <p 
                className="text-xs font-medium mb-1 text-gray-500"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
              >
                Teste ainda não iniciado
              </p>
              <p 
                className="text-micro text-center text-gray-400"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
              >
                O candidato receberá um convite para realizar o teste técnico.
              </p>
            </div>
          )}

          {status === 'in_progress' && (
            <div 
              className="flex flex-col items-center justify-center py-8"
              style={{ color: 'var(--status-warning)' }}
            >
              <Loader2 className="w-12 h-12 mb-3 animate-spin" />
              <p 
                className="text-xs font-medium mb-1 text-gray-500"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
              >
                Teste em andamento
              </p>
              <p 
                className="text-micro text-center text-gray-400"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
              >
                O candidato está realizando o teste técnico neste momento.
              </p>
            </div>
          )}
        </div>

        <div 
          className="px-4 py-3 flex justify-end border-t border-t-gray-100"
        >
          <Button
            onClick={onClose}
            size="sm"
            className="h-9 px-4 text-xs font-medium bg-gray-800 hover:bg-gray-900 text-white"
            style={{ fontFamily: "'Open Sans', sans-serif" }}
          >
            Fechar
          </Button>
        </div>
      </div>
    </div>
  )
}
