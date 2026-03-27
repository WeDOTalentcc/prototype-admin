"use client"

import React, { useState, useEffect, useRef } from "react"
import { Plus, Search, UserCheck, FileText, Calendar, MessageSquare, Bell, RefreshCcw, Brain, X, Move } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

interface PromptSuggestion {
  id: string
  icon: React.ElementType
  title: string
  description: string
  command: string
  category: "vagas" | "candidatos" | "entrevistas" | "relatorios"
}

const CATEGORY_COLORS = {
  vagas: {
    icon: 'var(--gray-600)',
    bg: 'var(--gray-50)',
    border: 'var(--gray-200)',
    hoverBg: 'var(--gray-100)'
  },
  candidatos: {
    icon: 'var(--status-success)',
    bg: 'var(--gray-50)',
    border: 'var(--status-success)',
    hoverBg: 'var(--gray-100)'
  },
  entrevistas: {
    icon: 'var(--wedo-orange)',
    bg: 'var(--gray-50)',
    border: 'var(--wedo-orange)',
    hoverBg: 'var(--gray-100)'
  },
  relatorios: {
    icon: 'var(--wedo-purple)',
    bg: 'var(--gray-50)',
    border: 'var(--wedo-purple)',
    hoverBg: 'var(--gray-100)'
  }
}

interface PromptSuggestionsDockProps {
  onSelect: (command: string) => void
  isEmpty: boolean
  onClose?: () => void
}

const DASHBOARD_SUGGESTIONS: PromptSuggestion[] = [
  {
    id: "create-job",
    icon: Plus,
    title: "Crie uma nova vaga",
    description: "Configure requisitos do sistema com descrição detalhada",
    command: "Criar uma nova vaga",
    category: "vagas"
  },
  {
    id: "approve-job",
    icon: FileText,
    title: "Solicite aprovação de nova vaga",
    description: "Encaminhe documentação para aprovação gerencial e justificativa",
    command: "Solicite aprovação de nova vaga",
    category: "vagas"
  },
  {
    id: "share-candidates",
    icon: UserCheck,
    title: "Compartilhe candidatos com gestor",
    description: "Crie relatório com perfis aprovados e recomendações",
    command: "Compartilhe candidatos com gestor",
    category: "candidatos"
  },
  {
    id: "search-candidates",
    icon: Search,
    title: "Buscar candidatos",
    description: "Encontre candidatos no banco de dados por perfil, skills ou experiência",
    command: "Buscar candidatos",
    category: "candidatos"
  },
  {
    id: "candidate-info",
    icon: Search,
    title: "Consulte sobre candidato",
    description: "Obtenha histórico específico e histórico completo",
    command: "Consulte informações sobre candidato",
    category: "candidatos"
  },
  {
    id: "add-candidate",
    icon: UserCheck,
    title: "Adicione novo candidato",
    description: "Cadastre perfil com talentos",
    command: "Adicione novo candidato",
    category: "candidatos"
  },
  {
    id: "reschedule-interview",
    icon: Calendar,
    title: "Reagende uma entrevista",
    description: "Cancele horário e notifique automaticamente participantes",
    command: "Reagende uma entrevista",
    category: "entrevistas"
  },
  {
    id: "update-status",
    icon: RefreshCcw,
    title: "Atualize status do candidato",
    description: "Modifique situação no processo e envie notificações",
    command: "Atualize status do candidato",
    category: "candidatos"
  }
]

export function PromptSuggestionsDock({ onSelect, isEmpty, onClose }: PromptSuggestionsDockProps) {
  const [isExpanded, setIsExpanded] = useState(isEmpty)
  
  const [position, setPosition] = useState({ top: 80, right: 24 })
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const cardRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const savedPosition = localStorage.getItem('lia-suggestions-position')
    if (savedPosition) {
      try {
        const parsed = JSON.parse(savedPosition)
        setPosition(parsed)
      } catch (e) {
        // Use default position
      }
    }
  }, [])

  useEffect(() => {
    localStorage.setItem('lia-suggestions-position', JSON.stringify(position))
  }, [position])

  React.useEffect(() => {
    if (!isEmpty) {
      setIsExpanded(false)
    }
  }, [isEmpty])

  const handleMouseDown = (e: React.MouseEvent) => {
    const targetElement = cardRef.current || buttonRef.current
    if (targetElement) {
      setIsDragging(true)
      const rect = targetElement.getBoundingClientRect()
      setDragOffset({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      })
    }
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      const newTop = e.clientY - dragOffset.y
      const newLeft = e.clientX - dragOffset.x
      
      const newRight = window.innerWidth - newLeft - (cardRef.current?.offsetWidth || 384)
      
      setPosition({
        top: Math.max(0, Math.min(newTop, window.innerHeight - 100)),
        right: Math.max(0, Math.min(newRight, window.innerWidth - 100))
      })
    }
  }

  const handleMouseUp = () => {
    setIsDragging(false)
  }

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, dragOffset])

  if (isEmpty) {
    return (
      <div className="w-full max-w-4xl mx-auto px-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 
              className="text-sm font-semibold flex items-center gap-2"
              style={{
                color: 'var(--gray-800)'
              }}
            >
              <div 
                className="p-1.5 rounded-md"
                className="bg-gray-900/[0.08]"
              >
                <Brain className="w-4 h-4 text-wedo-cyan" />
              </div>
              Tarefas Sugeridas
            </h3>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-3">
          {DASHBOARD_SUGGESTIONS.map((suggestion) => {
            const Icon = suggestion.icon
            const colors = CATEGORY_COLORS[suggestion.category]
            return (
              <button
                key={suggestion.id}
                onClick={() => onSelect(suggestion.command)}
                className="p-4 rounded-md transition-all text-left group"
                style={{ 
                  border: `1px solid ${colors.bg}`,
                  backgroundColor: 'var(--gray-50)',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = colors.hoverBg
                  e.currentTarget.style.borderColor = colors.border
                  e.currentTarget.style.transform = 'translateY(-2px)'
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--lia-bg-primary)'
                  e.currentTarget.style.borderColor = colors.bg
                  e.currentTarget.style.transform = 'translateY(0)'
                }}
              >
                <div className="flex items-start gap-3">
                  <div 
                    className="p-2 rounded-md flex-shrink-0"
                    style={{ backgroundColor: colors.bg }}
                  >
                    <Icon className="w-4 h-4" style={{ color: colors.icon }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 
                      className="font-semibold text-sm leading-tight mb-1"
                      style={{ 
                        color: 'var(--gray-800)',
                      }}
                    >
                      {suggestion.title}
                    </h3>
                    <p 
                      className="text-xs leading-snug line-clamp-2"
                      style={{ 
                        color: 'var(--gray-500)',
                      }}
                    >
                      {suggestion.description}
                    </p>
                  </div>
                </div>
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <>
      {!isExpanded && (
        <Button
          ref={buttonRef}
          variant="ghost"
          size="sm"
          onClick={() => setIsExpanded(true)}
          onMouseDown={handleMouseDown}
          className="fixed h-9 px-4 rounded-md transition-all hover:scale-105 z-50 select-none opacity-80 hover:opacity-100"
          style={{
            top: `${position.top}px`,
            right: `${position.right}px`,
            backgroundColor: 'var(--gray-50)',
            border: '1px solid var(--gray-200)',
            cursor: isDragging ? 'grabbing' : 'grab'
          }}
        >
          <div 
            className="p-1 rounded-md mr-2"
            className="bg-gray-900/[0.08]"
          >
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          </div>
          <span 
            className="text-xs font-medium"
            style={{ 
              color: 'var(--gray-500)',
            }}
          >
            Sugestões
          </span>
        </Button>
      )}

      {isExpanded && (
        <Card 
          ref={cardRef}
          className="fixed w-80 max-h-[480px] overflow-hidden z-50 select-none"
          style={{
            top: `${position.top}px`,
            right: `${position.right}px`,
            backgroundColor: 'var(--gray-50)',
            border: '1px solid var(--gray-200)',
            borderRadius: '16px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.12), 0 2px 8px rgba(0,0,0,0.08)'
          }}
        >
          {/* Header - Draggable */}
          <div 
            className="px-4 py-3 flex items-center justify-between border-b"
            onMouseDown={handleMouseDown}
            style={{ 
              backgroundColor: 'var(--gray-50)', 
              borderColor: 'var(--gray-200)',
              cursor: isDragging ? 'grabbing' : 'grab',
              borderRadius: '16px 16px 0 0'
            }}
          >
            <div className="flex items-center gap-2">
              <Move className="w-3 h-3 text-gray-300" />
              <div 
                className="p-1.5 rounded-md"
                className="bg-gray-900/[0.08]"
              >
                <Brain className="w-4 h-4 text-wedo-cyan" />
              </div>
              <h3 
                className="text-sm font-semibold"
                style={{ 
                  color: 'var(--gray-800)'
                }}
              >
                Tarefas Sugeridas
              </h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(false)}
              className="h-7 w-7 p-0 rounded-md hover:bg-gray-200"
            >
              <X className="w-4 h-4 text-gray-400" />
            </Button>
          </div>

          {/* Suggestions List */}
          <div className="p-3 space-y-2 overflow-y-auto max-h-[400px]">
            {DASHBOARD_SUGGESTIONS.map((suggestion) => {
              const Icon = suggestion.icon
              const colors = CATEGORY_COLORS[suggestion.category]
              return (
                <button
                  key={suggestion.id}
                  onClick={() => {
                    onSelect(suggestion.command)
                    setIsExpanded(false)
                  }}
                  className="w-full p-3 rounded-md transition-all text-left group"
                  style={{ 
                    backgroundColor: 'var(--gray-50)',
                    border: `1px solid ${colors.bg}`
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = colors.hoverBg
                    e.currentTarget.style.borderColor = colors.border
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--lia-bg-primary)'
                    e.currentTarget.style.borderColor = colors.bg
                  }}
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="p-2 rounded-md flex-shrink-0"
                      style={{ backgroundColor: colors.bg }}
                    >
                      <Icon className="w-4 h-4" style={{ color: colors.icon }} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 
                        className="font-medium text-sm leading-tight"
                        style={{ 
                          color: 'var(--gray-800)',
                        }}
                      >
                        {suggestion.title}
                      </h4>
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </Card>
      )}
    </>
  )
}
