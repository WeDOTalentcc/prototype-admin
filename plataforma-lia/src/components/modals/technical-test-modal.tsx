"use client"

import { X, Code, Clock, Trophy, Users, CheckCircle, Loader2, AlertCircle, TrendingUp, TrendingDown, Minus } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

interface TechnicalTestModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Record<string, unknown>
}

type TestStatus = 'pending' | 'in_progress' | 'completed'

const STATUS_CONFIG = {
  pending: {
    label: 'Pendente',
    icon: AlertCircle,
    color: 'var(--lia-text-tertiary)',
    bgColor: 'var(--lia-bg-tertiary)',
    borderColor: 'var(--lia-border-default)'
  },
  in_progress: {
    label: 'Em andamento',
    icon: Loader2,
    color: 'var(--status-warning)',
    bgColor: 'var(--status-warning-bg)',
    borderColor: 'var(--status-warning-border)'
  },
  completed: {
    label: 'Concluído',
    icon: CheckCircle,
    color: 'var(--status-success)',
    bgColor: 'var(--status-success-bg)',
    borderColor: 'var(--status-success-bg-15)'
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

  // @ts-ignore TODO: fix type
  const status: TestStatus = testData.status ?? 'pending'
  const statusConfig = STATUS_CONFIG[status]
  const StatusIcon = statusConfig.icon

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'var(--status-success)'
    if (score >= 60) return 'var(--lia-text-tertiary)'
    if (score >= 40) return 'var(--status-warning)'
    return 'var(--status-error)'
  }

  const getComparisonIcon = (candidateScore: number, avgScore: number) => {
    const diff = candidateScore - avgScore
    if (diff > 5) return <TrendingUp className="w-3 h-3 text-status-success"  />
    if (diff < -5) return <TrendingDown className="w-3 h-3 text-status-error"  />
    return <Minus className="w-3 h-3 text-lia-text-disabled" />
  }

  const getComparisonLabel = (candidateScore: number, avgScore: number) => {
    const diff = candidateScore - avgScore
    if (diff > 0) return `+${diff} acima da média`
    if (diff < 0) return `${diff} abaixo da média`
    return 'Na média'
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        className="w-full max-w-lg max-h-[85vh] overflow-hidden flex flex-col border border-lia-border-subtle bg-lia-bg-secondary rounded-md"
      >
        <div 
          className="flex items-center justify-between px-4 py-3 border-b border-b-lia-border-subtle"
        >
          <div className="flex items-center gap-2">
            <div
              className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-wedo-cyan/12"
            >
              <Code className="w-4 h-4 text-lia-text-secondary" />
            </div>
            <div>
              <h2 
                className="text-base-ui font-semibold text-lia-text-primary"
               
              >
                Teste Técnico
              </h2>
              <p 
                className="text-xs text-lia-text-secondary"
               
               // @ts-ignore TODO: fix type
               aria-live="polite" aria-atomic="true">
                {((candidate?.name ?? 'Candidato') as React.ReactNode)}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="h-7 w-7 p-0 flex items-center justify-center transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover rounded-full text-lia-text-tertiary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 bg-[var(--lia-bg-secondary)]">
          <div 
            className="flex items-center justify-between p-3 rounded-md mb-4"
            style={{backgroundColor: statusConfig.bgColor, border: `1px solid ${statusConfig.borderColor}`}}
          >
            <div className="flex items-center gap-2" role="status" aria-live="polite" aria-label="Carregando...">
              <StatusIcon 
                className={`w-4 h-4 ${status === 'in_progress' ? 'animate-spin motion-reduce:animate-none' : ''}`} 
                style={{color: statusConfig.color}} 
              />
              <span 
                className="text-xs font-medium"
                style={{color: statusConfig.color}}
              >
                {statusConfig.label}
              </span>
            </div>
            {(testData as any).completedAt && status === 'completed' && (
              <span 
                className="text-micro text-lia-text-secondary"
               
              // @ts-ignore TODO: fix type
              >
                Concluído em {new Date((testData as any).completedAt).toLocaleDateString('pt-BR')}
              </span>
            )}
          </div>

          {status === 'completed' && (
            // @ts-ignore TODO: fix type
            <>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div 
                  className="p-3 rounded-md border border-lia-border-subtle"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Trophy className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span 
                      className="text-micro text-lia-text-secondary"
                     
                    >
                      Score Geral
                    </span>
                  </div>
                  <span 
                    className="text-2xl font-bold"
                    // @ts-ignore TODO: fix type
                    style={{color: getScoreColor(testData.score)}}
                  // @ts-ignore TODO: fix type
                  >
                    {((testData as any).score as React.ReactNode)}
                  </span>
                  <span 
                    className="text-sm ml-1 text-lia-text-disabled"
                   
                  >
                    / 100
                  </span>
                </div>

                <div 
                  className="p-3 rounded-md border border-lia-border-subtle"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span 
                      className="text-micro text-lia-text-secondary"
                     
                    >
                      Tempo de Conclusão
                    </span>
                  </div>
                  <span 
                    className="text-2xl font-bold text-lia-text-primary"
                   
                  // @ts-ignore TODO: fix type
                  >
                    {((testData as any).duration as React.ReactNode)}
                  </span>
                  <span 
                    className="text-sm ml-1 text-lia-text-disabled"
                   
                  // @ts-ignore TODO: fix type
                  >
                    / {(testData as any).maxDuration} min
                  </span>
                </div>
              </div>

              <div className="flex items-center gap-2 p-3 rounded-md mb-4 bg-wedo-cyan/[.08] border border-wedo-cyan/20">
                <Users className="w-4 h-4 text-lia-text-secondary" />
                <span 
                  className="text-xs text-lia-text-secondary"
                 
                 aria-live="polite" aria-atomic="true">
                  Comparação com outros candidatos:
                </span>
                <span 
                  className="text-xs font-semibold ml-auto"
                  // @ts-ignore TODO: fix type
                  style={{color: testData.score >= testData.averageScore ? 'var(--status-success)' : 'var(--status-error)'}}
                // @ts-ignore TODO: fix type
                >
                  {(getComparisonLabel((testData as any).score, (testData as any).averageScore) as React.ReactNode)}
                </span>
              </div>

              <div className="mb-4">
                <p 
                  className="text-xs font-semibold mb-3 text-lia-text-primary"
                 
                >
                  Breakdown por Categoria
                </p>


                <div className="space-y-2.5">
                  {((testData as any).categories as any[])?.map((category: Record<string, unknown>, index: number) => (
                    <div 
                      key={index}
                      className="p-3 rounded-md border border-lia-border-subtle"

                    >
                      <div className="flex items-center justify-between mb-2">
                        <span 
                          className="text-xs font-medium text-lia-text-primary"
                         
                        >
                          {(category.name as React.ReactNode)}
                        </span>

                        <div className="flex items-center gap-2">
                          {(getComparisonIcon((category as any).score, (category as any).avgScore) as React.ReactNode)}
                          <span 

                            className="text-xs font-bold"
                            // @ts-ignore TODO: fix type
                            style={{color: getScoreColor((category as any).score)}}
                          >
                            {(category.score as React.ReactNode)}
                          </span>
                        </div>
                      </div>
                      <div className="relative">
                        <Progress 
                          // @ts-ignore TODO: fix type
                          value={category.score} 
                          className="h-1.5 bg-lia-interactive-active"
                        />
                        <div 
                          className="absolute top-0 h-1.5 rounded-full opacity-30 bg-lia-border-medium" style={{width: `${category.avgScore}%`}}
                        />
                      </div>
                      <div className="flex items-center justify-between mt-1">
                        <span 
                          className="text-micro text-lia-text-secondary"
                         
                         // @ts-ignore TODO: fix type
                         aria-live="polite" aria-atomic="true">
                          Média dos candidatos: {(category.avgScore as React.ReactNode)}
                        </span>
                        <span 
                          className="text-micro"
                          style={{color: (category as any).score >= (category as any).avgScore ? 'var(--status-success)' : 'var(--status-error)'}}
                        >
                          {(category as any).score >= (category as any).avgScore ? '+' : ''}{(category as any).score - (category as any).avgScore}
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
              className="flex flex-col items-center justify-center py-8 text-lia-text-disabled"
            >
              <AlertCircle className="w-12 h-12 mb-3" />
              <p 
                className="text-xs font-medium mb-1 text-lia-text-tertiary"
               
              >
                Teste ainda não iniciado
              </p>
              <p 
                className="text-micro text-center text-lia-text-disabled"
                // @ts-ignore TODO: fix type
               
               aria-live="polite" aria-atomic="true">
                O candidato receberá um convite para realizar o teste técnico.
              </p>
            </div>
          )}

          {status === 'in_progress' && (
            <div 
              className="flex flex-col items-center justify-center py-8 text-status-warning"
              
            >
              <Loader2 className="w-12 h-12 mb-3 animate-spin motion-reduce:animate-none" />
              <p 
                className="text-xs font-medium mb-1 text-lia-text-tertiary"
               
              >
                Teste em andamento
              </p>
              <p 
                className="text-micro text-center text-lia-text-disabled"
               
               aria-live="polite" aria-atomic="true">
                O candidato está realizando o teste técnico neste momento.
              </p>
            </div>
          )}
        </div>

        <div 
          className="px-4 py-3 flex justify-end border-t border-t-lia-border-subtle"
        >
          <Button
            onClick={onClose}
            size="sm"
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-white"
           
          >
            Fechar
          </Button>
        </div>
      </div>
    </div>
  )
}
