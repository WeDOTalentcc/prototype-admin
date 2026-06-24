"use client"

import { X, Globe, CheckCircle, Loader2, AlertCircle, BookOpen, Pencil, MessageCircle, Headphones } from "lucide-react"
import { getPercentageScoreVar, getEnglishLevel } from "@/lib/score-utils"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

type TestStatus = 'pending' | 'in_progress' | 'completed'

interface EnglishTestData {
  status?: TestStatus
  score?: number
  level?: string
  completedAt?: string
  skills?: Record<string, number>
}

interface EnglishTestModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Record<string, unknown>
}

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

const SKILL_CONFIG = [
  { id: 'reading', label: 'Leitura', icon: BookOpen },
  { id: 'writing', label: 'Escrita', icon: Pencil },
  { id: 'speaking', label: 'Conversação', icon: MessageCircle },
  { id: 'listening', label: 'Compreensão', icon: Headphones },
]

const LEVEL_CONFIG: Record<string, { label: string; description: string; color: string; bgColor: string; borderColor: string }> = {
  'A1': { label: 'A1 - Iniciante', description: 'Nível básico inicial', color: 'var(--status-error)', bgColor: 'var(--status-error-bg)', borderColor: 'var(--status-error-border)' },
  'A2': { label: 'A2 - Básico', description: 'Nível básico', color: 'var(--status-warning)', bgColor: 'var(--status-warning-bg)', borderColor: 'var(--status-warning-border)' },
  'B1': { label: 'B1 - Intermediário', description: 'Nível intermediário', color: 'var(--status-warning)', bgColor: 'var(--status-warning-bg)', borderColor: 'var(--status-warning-border)' },
  'B2': { label: 'B2 - Intermediário Superior', description: 'Nível intermediário avançado', color: 'var(--lia-text-secondary)', bgColor: 'var(--lia-bg-tertiary)', borderColor: 'var(--lia-border-default)' },
  'C1': { label: 'C1 - Avançado', description: 'Nível avançado', color: 'var(--status-success)', bgColor: 'var(--status-success-bg)', borderColor: 'var(--status-success-bg-15)' },
  'C2': { label: 'C2 - Proficiente', description: 'Nível de proficiência nativa', color: 'var(--status-success)', bgColor: 'var(--status-success-bg)', borderColor: 'var(--status-success-bg-15)' },
}

export function EnglishTestModal({ isOpen, onClose, candidate }: EnglishTestModalProps) {
  if (!isOpen) return null

  const testData: EnglishTestData = (candidate?.englishTest as EnglishTestData) ?? {
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
  const levelInfo = LEVEL_CONFIG[testData.level ?? 'B1'] ?? LEVEL_CONFIG['B1']

  const getScoreColor = getPercentageScoreVar

  const getSkillLevel = getEnglishLevel

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-lia-overlay"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      data-testid="english-test-modal"
    >
      <div 
        className="w-full max-w-lg max-h-[85vh] overflow-hidden flex flex-col bg-lia-bg-primary border border-lia-border-subtle rounded-xl"
        
      >
        <div 
          className="flex items-center justify-between px-4 py-3 bg-lia-bg-secondary rounded-t-xl"
        >
          <div className="flex items-center gap-2">
            <div 
              className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-blue-500/10"
            >
              <Globe className="w-4 h-4 text-[var(--lia-text-secondary)]" />
            </div>
            <div>
              <h2 
                className="text-base-ui font-semibold text-lia-text-primary"
               
              >
                Teste de Inglês
              </h2>
              <p 
                className="text-xs text-lia-text-tertiary"
               
               aria-live="polite" aria-atomic="true">
                {((candidate?.name ?? 'Candidato') as React.ReactNode)}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="h-7 w-7 p-0 flex items-center justify-center transition-colors motion-reduce:transition-none hover:bg-lia-interactive-hover dark:hover:bg-lia-btn-primary-bg rounded-full text-lia-text-tertiary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 bg-lia-bg-primary">
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
            {(testData).completedAt && status === 'completed' && (
              <span 
                className="text-micro text-lia-text-tertiary"
              >
                Concluído em {new Date((testData).completedAt).toLocaleDateString('pt-BR')}
              </span>
            )}
          </div>

          {status === 'completed' && (
            <>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div 
                  className="p-3 rounded-xl border border-lia-border-subtle"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Globe className="w-3.5 h-3.5 text-lia-text-secondary" />
                    <span 
                      className="text-micro text-lia-text-tertiary"
                     
                    >
                      Score Geral
                    </span>
                  </div>
                  <span 
                    className="text-2xl font-semibold"
                    style={{color: getScoreColor((testData).score ?? 0)}}
                  >
                    {((testData).score as React.ReactNode)}
                  </span>
                  <span 
                    className="text-sm ml-1 text-lia-text-disabled"
                   
                  >
                    / 100
                  </span>
                </div>

                <div 
                  className="p-3 rounded-md"
                  style={{backgroundColor: levelInfo.bgColor, border: `1px solid ${levelInfo.borderColor}`}}
                >
                  <div className="flex items-center gap-2 mb-1">
                    <span 
                      className="text-micro text-lia-text-tertiary"
                     
                    >
                      Nível CEFR
                    </span>
                  </div>
                  <span 
                    className="text-lg font-semibold"
                    style={{color: levelInfo.color}}
                  >
                    {((testData).level as React.ReactNode)}
                  </span>
                  <p 
                    className="text-micro mt-0.5 text-lia-text-secondary"
                   
                  >
                    {levelInfo.description}
                  </p>
                </div>
              </div>

              <div className="mb-4">
                <p 
                  className="text-xs font-semibold mb-3 text-lia-text-primary"
                 
                >
                  Breakdown por Habilidade
                </p>

                <div className="space-y-2.5">
                  {SKILL_CONFIG.map((skill) => {
                    const Icon = skill.icon
                    const score = (testData).skills?.[skill.id] ?? 0
                    const skillLevel = getSkillLevel(score)

                    return (
                      <div 
                        key={skill.id}
                        className="p-3 rounded-xl border border-lia-border-subtle"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Icon className="w-3.5 h-3.5 text-lia-text-secondary" />
                            <span 
                              className="text-xs font-medium text-lia-text-primary"
                             
                            >
                              {skill.label}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span 
                              className="text-micro px-1.5 py-0.5 rounded-full font-medium"
                              style={{color: LEVEL_CONFIG[skillLevel]?.color ?? 'var(--lia-text-tertiary)',
                                backgroundColor: LEVEL_CONFIG[skillLevel]?.bgColor ?? 'var(--lia-bg-tertiary)'}}
                            >
                              {skillLevel}
                            </span>
                            <span 
                              className="text-xs font-bold"
                              style={{color: getScoreColor(score)}}
                            >
                              {score}
                            </span>
                          </div>
                        </div>
                        <Progress 
                          value={score} 
                          className="h-2 bg-lia-interactive-active"
                        />
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="p-3 rounded-xl bg-wedo-cyan/[.08] border border-wedo-cyan/20">
                <p 
                  className="text-micro font-medium mb-1 text-lia-text-secondary"
                 
                >
                  Sobre o nível CEFR
                </p>
                <p 
                  className="text-micro text-lia-text-secondary"
                 
                >
                  O CEFR (Quadro Europeu Comum de Referência) é um padrão internacional para descrever habilidades linguísticas em uma escala de A1 (iniciante) a C2 (proficiente).
                </p>
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
                className="text-micro text-center text-lia-text-muted"
               
               aria-live="polite" aria-atomic="true">
                O candidato receberá um convite para realizar o teste de inglês.
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
                className="text-micro text-center text-lia-text-muted"
               
               aria-live="polite" aria-atomic="true">
                O candidato está realizando o teste de inglês neste momento.
              </p>
            </div>
          )}
        </div>

        <div 
          className="px-4 py-3 flex justify-end bg-lia-bg-secondary border-t border-lia-border-subtle rounded-b-xl"
        >
          <Button
            onClick={onClose}
            size="sm"
            className="h-9 px-4 text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text dark:hover:bg-lia-interactive-active"
          >
            Fechar
          </Button>
        </div>
      </div>
    </div>
  )
}
