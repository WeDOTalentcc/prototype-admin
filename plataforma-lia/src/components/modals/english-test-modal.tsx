// @ts-nocheck
"use client"

import { X, Globe, CheckCircle, Loader2, AlertCircle, BookOpen, Pencil, MessageCircle, Headphones } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"

interface EnglishTestModalProps {
  isOpen: boolean
  onClose: () => void
  candidate: Record<string, unknown>
}

type TestStatus = 'pending' | 'in_progress' | 'completed'

const STATUS_CONFIG = {
  pending: {
    label: 'Pendente',
    icon: AlertCircle,
    color: 'var(--gray-400)',
    bgColor: 'var(--gray-bg-10)',
    borderColor: 'var(--gray-border)'
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
  'B2': { label: 'B2 - Intermediário Superior', description: 'Nível intermediário avançado', color: 'var(--gray-600)', bgColor: 'var(--gray-600-bg-10)', borderColor: 'var(--gray-border)' },
  'C1': { label: 'C1 - Avançado', description: 'Nível avançado', color: 'var(--status-success)', bgColor: 'var(--status-success-bg)', borderColor: 'var(--status-success-bg-15)' },
  'C2': { label: 'C2 - Proficiente', description: 'Nível de proficiência nativa', color: 'var(--status-success)', bgColor: 'var(--status-success-bg)', borderColor: 'var(--status-success-bg-15)' },
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
    if (score >= 80) return 'var(--status-success)'
    if (score >= 60) return 'var(--gray-600)'
    if (score >= 40) return 'var(--status-warning)'
    return 'var(--status-error)'
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
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div 
        className="w-full max-w-lg max-h-[85vh] overflow-hidden flex flex-col bg-white dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle rounded-md"
        
      >
        <div 
          className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-lia-bg-primary border-b border-lia-border-subtle dark:border-lia-border-subtle rounded-t-xl"
        >
          <div className="flex items-center gap-2">
            <div 
              className="w-8 h-8 rounded-md flex items-center justify-center flex-shrink-0 bg-blue-500/10"
            >
              <Globe className="w-4 h-4" className="text-[var(--gray-600)]" />
            </div>
            <div>
              <h2 
                className="text-base-ui font-semibold text-lia-text-primary dark:text-lia-text-primary"
               
              >
                Teste de Inglês
              </h2>
              <p 
                className="text-xs text-lia-text-tertiary"
               
               aria-live="polite" aria-atomic="true">
                {candidate?.name ?? 'Candidato'}
              </p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="h-7 w-7 p-0 flex items-center justify-center transition-colors motion-reduce:transition-none hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full text-lia-text-tertiary dark:text-lia-text-tertiary"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 py-4 bg-white dark:bg-lia-bg-primary">
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
            {testData.completedAt && status === 'completed' && (
              <span 
                className="text-micro text-lia-text-tertiary"
               
              >
                Concluído em {new Date(testData.completedAt).toLocaleDateString('pt-BR')}
              </span>
            )}
          </div>

          {status === 'completed' && (
            <>
              <div className="grid grid-cols-2 gap-3 mb-4">
                <div 
                  className="p-3 rounded-md border border-lia-border-subtle"
                >
                  <div className="flex items-center gap-2 mb-1">
                    <Globe className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                    <span 
                      className="text-micro text-lia-text-tertiary"
                     
                    >
                      Score Geral
                    </span>
                  </div>
                  <span 
                    className="text-2xl font-bold"
                    style={{color: getScoreColor(testData.score)}}
                  >
                    {testData.score}
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
                    className="text-lg font-bold"
                    style={{color: levelInfo.color}}
                  >
                    {testData.level}
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
                  className="text-xs font-semibold mb-3 text-lia-text-primary dark:text-lia-text-primary"
                 
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
                        className="p-3 rounded-md border border-lia-border-subtle"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Icon className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
                            <span 
                              className="text-xs font-medium text-lia-text-primary dark:text-lia-text-primary"
                             
                            >
                              {skill.label}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span 
                              className="text-micro px-1.5 py-0.5 rounded-full font-medium"
                              style={{color: LEVEL_CONFIG[skillLevel]?.color ?? 'var(--gray-400)',
                                backgroundColor: LEVEL_CONFIG[skillLevel]?.bgColor ?? 'var(--gray-bg-10)'}}
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
                          className="h-2 bg-gray-200"
                        />
                      </div>
                    )
                  })}
                </div>
              </div>

              <div className="p-3 rounded-md bg-wedo-cyan/[.08] border border-wedo-cyan/20">
                <p 
                  className="text-micro font-medium mb-1 text-lia-text-secondary dark:text-lia-text-secondary"
                 
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
                className="text-micro text-center text-lia-text-disabled"
               
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
                className="text-micro text-center text-lia-text-disabled"
               
               aria-live="polite" aria-atomic="true">
                O candidato está realizando o teste de inglês neste momento.
              </p>
            </div>
          )}
        </div>

        <div 
          className="px-4 py-3 flex justify-end bg-gray-50 dark:bg-lia-bg-primary border-t border-lia-border-subtle dark:border-lia-border-subtle rounded-b-xl"
        >
          <Button
            onClick={onClose}
            size="sm"
            className="h-9 px-4 text-xs font-medium bg-gray-900 hover:bg-gray-800 text-white dark:bg-gray-50 dark:text-lia-text-disabled dark:hover:bg-gray-200"
          >
            Fechar
          </Button>
        </div>
      </div>
    </div>
  )
}
