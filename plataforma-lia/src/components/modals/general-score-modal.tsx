"use client"

import { X, Gauge, TrendingUp, FileText, Brain, Code, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

interface GeneralScoreModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: any
}

const SCORE_COMPONENTS = [
  { 
    id: 'cv_fit', 
    label: 'CV / Fit Score', 
    weight: 25, 
    icon: FileText,
    description: 'Aderência do currículo ao perfil da vaga'
  },
  { 
    id: 'triagem_lia', 
    label: 'Triagem LIA', 
    weight: 30, 
    icon: Brain,
    description: 'Avaliação da conversa de triagem com a LIA'
  },
  { 
    id: 'teste_tecnico', 
    label: 'Teste Técnico', 
    weight: 25, 
    icon: Code,
    description: 'Desempenho no teste técnico aplicado'
  },
  { 
    id: 'teste_ingles', 
    label: 'Teste de Inglês', 
    weight: 20, 
    icon: Globe,
    description: 'Nível de proficiência em inglês'
  },
]

export function GeneralScoreModal({ isOpen, onClose, candidate }: GeneralScoreModalProps) {
  if (!isOpen) return null

  const scores = {
    cv_fit: candidate?.cvFitScore ?? candidate?.fitScore ?? 85,
    triagem_lia: candidate?.triagemScore ?? candidate?.screeningScore ?? 92,
    teste_tecnico: candidate?.technicalScore ?? candidate?.testeTecnico ?? 78,
    teste_ingles: candidate?.englishScore ?? candidate?.testeIngles ?? 72,
  }

  const calculateWeightedScore = () => {
    let totalWeightedScore = 0
    let totalWeight = 0

    SCORE_COMPONENTS.forEach(component => {
      const score = scores[component.id as keyof typeof scores]
      if (score !== null && score !== undefined) {
        totalWeightedScore += score * (component.weight / 100)
        totalWeight += component.weight
      }
    })

    if (totalWeight === 0) return 0
    return Math.round((totalWeightedScore / totalWeight) * 100)
  }

  const finalScore = candidate?.score ?? calculateWeightedScore()

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'var(--status-success)'
    if (score >= 60) return 'var(--gray-400)'
    if (score >= 40) return 'var(--status-warning)'
    return 'var(--status-error)'
  }

  const getScoreLabel = (score: number) => {
    if (score >= 90) return 'Excelente'
    if (score >= 80) return 'Muito Bom'
    if (score >= 70) return 'Bom'
    if (score >= 60) return 'Satisfatório'
    if (score >= 50) return 'Regular'
    return 'Abaixo do esperado'
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4" 
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div 
        className="w-full max-w-2xl overflow-hidden flex flex-col bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md"
        style={{ 
          boxShadow: '0 16px 32px -8px rgba(0, 0, 0, 0.12)'
        }}
      >
        <div 
          className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 rounded-t-xl"
        >
          <div className="flex items-center gap-2">
            <div 
              className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0"
              style={{ backgroundColor: 'rgba(96, 190, 209, 0.12)' }}
            >
              <Gauge className="w-4 h-4 text-gray-700" />
            </div>
            <div>
              <h2 
                className="text-sm font-semibold text-gray-950 dark:text-gray-50"
               
              >
                Nota Geral LIA
              </h2>
              <p 
                className="text-xs text-gray-600"
               
              >
                Metodologia de cálculo do score
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="h-7 w-7 p-0 flex items-center justify-center transition-colors hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full text-gray-500 dark:text-gray-400"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="px-4 py-4 bg-white dark:bg-gray-900">
          <div 
            className="flex items-center justify-between p-4 rounded-md mb-4 border border-gray-100"
          >
            <div>
              <p 
                className="text-micro uppercase tracking-wide mb-1 text-gray-600"
               
              >
                Nota Final
              </p>
              <div className="flex items-baseline gap-2">
                <span 
                  className="text-3xl font-bold"
                  style={{ color: getScoreColor(finalScore) }}
                >
                  {finalScore}
                </span>
                <span 
                  className="text-sm text-gray-500"
                 
                >
                  / 100
                </span>
              </div>
            </div>
            <div className="text-right">
              <span 
                className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium rounded-full"
                style={{ 
                  backgroundColor: `${getScoreColor(finalScore)}15`,
                  color: getScoreColor(finalScore),
                }}
              >
                <TrendingUp className="w-3 h-3" />
                {getScoreLabel(finalScore)}
              </span>
            </div>
          </div>

          <div className="mb-3">
            <p 
              className="text-xs font-semibold mb-3 text-gray-950 dark:text-gray-50"
             
            >
              Composição do Score (Média Ponderada)
            </p>

            <div className="space-y-3">
              {SCORE_COMPONENTS.map((component) => {
                const Icon = component.icon
                const score = scores[component.id as keyof typeof scores]
                const hasScore = score !== null && score !== undefined

                return (
                  <div 
                    key={component.id}
                    className="p-3 rounded-md border border-gray-100"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Icon className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                        <span 
                          className="text-xs font-medium text-gray-950 dark:text-gray-50"
                         
                        >
                          {component.label}
                        </span>
                        <span 
                          className="text-micro px-1.5 py-0.5 rounded-full text-gray-700 bg-gray-200"
                        >
                          Peso: {component.weight}%
                        </span>
                      </div>
                      <span 
                        className="text-xs font-bold"
                        style={{ 
                          
                          color: hasScore ? getScoreColor(score) : 'var(--gray-400)'
                        }}
                      >
                        {hasScore ? `${score}` : 'N/A'}
                      </span>
                    </div>
                    <Progress 
                      value={hasScore ? score : 0} 
                      className="h-1.5 bg-gray-200" style={{ ['--progress-color' as any]: hasScore ? getScoreColor(score) : 'var(--gray-200)' }}
                    />
                    <p 
                      className="text-micro mt-1.5 text-gray-600"
                     
                    >
                      {component.description}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>

          <div 
            className="p-3 rounded-md"
            style={{ backgroundColor: 'rgba(96, 190, 209, 0.08)', border: '1px solid rgba(96, 190, 209, 0.2)' }}
          >
            <p 
              className="text-micro font-medium mb-1 text-gray-700 dark:text-gray-300"
             
            >
              Fórmula do cálculo:
            </p>
            <p 
              className="text-micro text-gray-600"
             
            >
              Score = (CV × 0.25) + (Triagem × 0.30) + (Técnico × 0.25) + (Inglês × 0.20)
            </p>
          </div>
        </div>

        <div 
          className="px-4 py-3 flex justify-end bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 rounded-b-xl"
        >
          <Button
            onClick={onClose}
            size="sm"
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            Entendido
          </Button>
        </div>
      </div>
    </div>
  )
}
