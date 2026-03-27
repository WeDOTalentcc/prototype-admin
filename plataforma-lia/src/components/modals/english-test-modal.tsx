"use client"

import { X, Globe, CheckCircle, Loader2, AlertCircle, BookOpen, Pencil, MessageCircle, Headphones } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

interface EnglishTestModalProps {
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

const SKILL_CONFIG = [
  { id: 'reading', label: 'Leitura', icon: BookOpen },
  { id: 'writing', label: 'Escrita', icon: Pencil },
  { id: 'speaking', label: 'Conversação', icon: MessageCircle },
  { id: 'listening', label: 'Compreensão', icon: Headphones },
]

const LEVEL_CONFIG: Record<string, { label: string; description: string; color: string }> = {
  'A1': { label: 'A1 - Iniciante', description: 'Nível básico inicial', color: 'var(--status-error)' },
  'A2': { label: 'A2 - Básico', description: 'Nível básico', color: 'var(--status-warning)' },
  'B1': { label: 'B1 - Intermediário', description: 'Nível intermediário', color: 'var(--status-warning)' },
  'B2': { label: 'B2 - Intermediário Superior', description: 'Nível intermediário avançado', color: '#3B82F6' },
  'C1': { label: 'C1 - Avançado', description: 'Nível avançado', color: 'var(--status-success)' },
  'C2': { label: 'C2 - Proficiente', description: 'Nível de proficiência nativa', color: 'var(--status-success)' },
}

export function EnglishTestModal({ isOpen, onClose, candidate }: EnglishTestModalProps) {
  if (!isOpen) return null

  const testData = candidate?.englishTest ?? {
    status: 'completed',
    score: 75,
    level: 'B2',
    completedAt: '2024-01-14',
    skills: {
      reading: 80,
      writing: 78,
      speaking: 70,
      listening: 72,
    }
  }

  const status: TestStatus = testData.status ?? 'pending'
  const statusConfig = STATUS_CONFIG[status]
  const StatusIcon = statusConfig.icon
  const levelInfo = LEVEL_CONFIG[testData.level] ?? LEVEL_CONFIG['B1']

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#10B981'
    if (score >= 60) return '#3B82F6'
    if (score >= 40) return '#F59E0B'
    return '#EF4444'
  }

  const getSkillLevel = (score: number) => {
    if (score >= 90) return 'C2'
    if (score >= 80) return 'C1'
    if (score >= 70) return 'B2'
    if (score >= 60) return 'B1'
    if (score >= 40) return 'A2'
    return 'A1'
  }

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4" 
      style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div 
        className="w-full max-w-lg max-h-[85vh] overflow-hidden flex flex-col bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-md"
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
              style={{ backgroundColor: 'rgba(59, 130, 246, 0.12)' }}
            >
              <Globe className="w-4 h-4" style={{ color: '#3B82F6' }} />
            </div>
            <div>
              <h2 
                className="text-base-ui font-semibold text-gray-950 dark:text-gray-50"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
              >
                Teste de Inglês
              </h2>
              <p 
                className="text-xs text-gray-500"
                style={{ fontFamily: "'Open Sans', sans-serif" }}
              >
                {candidate?.name ?? 'Candidato'}
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

        <div className="flex-1 overflow-y-auto px-4 py-4 bg-white dark:bg-gray-900">
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
                className="text-micro text-gray-500"
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
                    <Globe className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                    <span 
                      className="text-micro text-gray-500"
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
                  className="p-3 rounded-md"
                  style={{ backgroundColor: `${levelInfo.color}10`, border: `1px solid ${levelInfo.color}30` }}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span 
                      className="text-micro text-gray-500"
                      style={{ fontFamily: "'Open Sans', sans-serif" }}
                    >
                      Nível CEFR
                    </span>
                  </div>
                  <span 
                    className="text-lg font-bold"
                    style={{ fontFamily: "'Open Sans', sans-serif", color: levelInfo.color }}
                  >
                    {testData.level}
                  </span>
                  <p 
                    className="text-micro mt-0.5 text-gray-600"
                    style={{ fontFamily: "'Open Sans', sans-serif" }}
                  >
                    {levelInfo.description}
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <p 
                  className="text-xs font-semibold mb-3 text-gray-950 dark:text-gray-50"
                  style={{ fontFamily: "'Open Sans', sans-serif" }}
                >
                  Breakdown por Habilidade
                </p>

                <div className="space-y-2.5">
                  {SKILL_CONFIG.map((skill) => {
                    const Icon = skill.icon
                    const score = testData.skills?.[skill.id] ?? 0
                    const skillLevel = getSkillLevel(score)

                    return (
                      <div 
                        key={skill.id}
                        className="p-3 rounded-md border border-gray-100"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Icon className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
                            <span 
                              className="text-xs font-medium text-gray-950 dark:text-gray-50"
                              style={{ fontFamily: "'Open Sans', sans-serif" }}
                            >
                              {skill.label}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span 
                              className="text-micro px-1.5 py-0.5 rounded-full font-medium"
                              style={{ 
                                fontFamily: "'Open Sans', sans-serif", 
                                color: LEVEL_CONFIG[skillLevel]?.color ?? '#6B7280',
                                backgroundColor: `${LEVEL_CONFIG[skillLevel]?.color ?? '#6B7280'}15`
                              }}
                            >
                              {skillLevel}
                            </span>
                            <span 
                              className="text-xs font-bold"
                              style={{ fontFamily: "'Open Sans', sans-serif", color: getScoreColor(score) }}
                            >
                              {score}
                            </span>
                          </div>
                        </div>
                        <Progress 
                          value={score} 
                          className="h-2 bg-gray-200"
                        />
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
                  style={{ fontFamily: "'Open Sans', sans-serif" }}
                >
                  Sobre o nível CEFR
                </p>
                <p 
                  className="text-micro text-gray-600"
                  style={{ fontFamily: "'Open Sans', sans-serif" }}
                >
                  O CEFR (Quadro Europeu Comum de Referência) é um padrão internacional para descrever habilidades linguísticas em uma escala de A1 (iniciante) a C2 (proficiente).
                </p>
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
                O candidato receberá um convite para realizar o teste de inglês.
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
                O candidato está realizando o teste de inglês neste momento.
              </p>
            </div>
          )}
        </div>

        <div 
          className="px-4 py-3 flex justify-end bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 rounded-b-xl"
        >
          <Button
            onClick={onClose}
            size="sm"
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-gray-900 dark:hover:bg-gray-200"
          >
            Fechar
          </Button>
        </div>
      </div>
    </div>
  )
}
