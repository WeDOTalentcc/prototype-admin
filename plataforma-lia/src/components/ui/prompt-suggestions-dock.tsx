"use client"

import React, { useState, useEffect, useRef } from "react"
import { Plus, Search, UserCheck, FileText, Calendar, MessageSquare, Bell, RefreshCcw, Brain, X, Move } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useUIPreferencesStore } from "@/stores/ui-preferences-store"

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
    icon: 'var(--lia-text-secondary)',
    bg: 'var(--lia-bg-secondary)',
    border: 'var(--lia-border-subtle)',
    hoverBg: 'var(--lia-bg-tertiary)'
  },
  candidatos: {
    icon: 'var(--status-success)',
    bg: 'var(--lia-bg-secondary)',
    border: 'var(--status-success)',
    hoverBg: 'var(--lia-bg-tertiary)'
  },
  entrevistas: {
    icon: 'var(--wedo-orange)',
    bg: 'var(--lia-bg-secondary)',
    border: 'var(--wedo-orange)',
    hoverBg: 'var(--lia-bg-tertiary)'
  },
  relatorios: {
    icon: 'var(--wedo-purple)',
    bg: 'var(--lia-bg-secondary)',
    border: 'var(--wedo-purple)',
    hoverBg: 'var(--lia-bg-tertiary)'
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
  
  const storePosition = useUIPreferencesStore((s) => s.promptSuggestionsPosition)
  const setStorePosition = useUIPreferencesStore((s) => s.setPromptSuggestionsPosition)
  const [position, setPositionLocal] = useState(storePosition)
  const [isDragging, setIsDragging] = useState(false)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const buttonRef = useRef<HTMLButtonElement>(null)
  const cardRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setPositionLocal(storePosition)
  }, [storePosition])

  const setPosition = (pos: { top: number; right: number }) => {
    setPositionLocal(pos)
    setStorePosition(pos)
  }

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
      <div className="w-full">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {DASHBOARD_SUGGESTIONS.map((suggestion) => {
            const Icon = suggestion.icon
            return (
              <button
                key={suggestion.id}
                onClick={() => onSelect(suggestion.command)}
                className="flex items-center gap-3 p-3 text-left border border-lia-border-subtle rounded-xl bg-white transition-all duration-200 hover:scale-[1.02] hover:border-wedo-cyan/40 hover:shadow-sm group"
              >
                <div className="bg-wedo-cyan/[0.08] text-wedo-cyan rounded-lg p-1.5 transition-colors group-hover:bg-wedo-cyan/[0.15] flex-shrink-0">
                  <Icon className="w-4 h-4" />
                </div>
                <span className="text-sm font-medium text-lia-text-secondary group-hover:text-lia-text-primary">
                  {suggestion.title}
                </span>
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
          className="fixed h-9 px-4 rounded-md transition-transform motion-reduce:transition-none hover:scale-105 z-50 select-none opacity-80 hover:opacity-100"
          style={{top: `${position.top}px`,
            right: `${position.right}px`,
            backgroundColor: 'var(--lia-bg-secondary)',
            border: '1px solid var(--lia-border-subtle)',
            cursor: isDragging ? 'grabbing' : 'grab'}}
        >
          <div className="p-1 rounded-md mr-2 bg-lia-btn-primary-bg/[0.08]">
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
          </div>
          <span 
            className="text-xs font-medium"
            style={{color: 'var(--lia-text-secondary)'}}
          >
            Sugestões
          </span>
        </Button>
      )}

      {isExpanded && (
        <Card
          ref={cardRef}
          className="fixed w-80 max-h-[480px] overflow-hidden z-50 select-none rounded-md border border-lia-border-subtle bg-lia-bg-secondary"
          style={{top: `${position.top}px`,
            right: `${position.right}px`}}
        >
          {/* Header - Draggable */}
          <div
            className="px-4 py-3 flex items-center justify-between border-b rounded-t-md"
            onMouseDown={handleMouseDown}
            style={{backgroundColor: 'var(--lia-bg-secondary)',
              borderColor: 'var(--lia-border-subtle)',
              cursor: isDragging ? 'grabbing' : 'grab'}}
          >
            <div className="flex items-center gap-2">
              <Move className="w-3 h-3 text-lia-text-tertiary" />
              <div className="p-1.5 rounded-md bg-lia-btn-primary-bg/[0.08]">
                <Brain className="w-4 h-4 text-wedo-cyan" />
              </div>
              <h3
                className="text-sm font-semibold"
                style={{color: 'var(--lia-text-primary)'}}
              >
                Tarefas Sugeridas
              </h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsExpanded(false)}
              className="h-7 w-7 p-0 rounded-md hover:bg-lia-interactive-active"
            >
              <X className="w-4 h-4 text-lia-text-secondary" />
            </Button>
          </div>

          {/* Suggestions List */}
          <div className="p-3 space-y-2 overflow-y-auto max-h-content-lg">
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
                  className="w-full p-2.5 rounded-md transition-colors motion-reduce:transition-none text-left group"
                  style={{backgroundColor: 'var(--white)',
                    border: `1px solid ${colors.bg}`}}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = colors.hoverBg
                    e.currentTarget.style.borderColor = colors.border
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = 'var(--white)'
                    e.currentTarget.style.borderColor = colors.bg
                  }}
                >
                  <div className="flex items-center gap-2.5">
                    <div 
                      className="p-1.5 rounded-md flex-shrink-0"
                      style={{backgroundColor: colors.bg}}
                    >
                      <Icon className="w-3.5 h-3.5" style={{color: colors.icon}} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 
                        className="font-medium text-xs leading-tight"
                        style={{color: 'var(--lia-text-primary)'}}
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
