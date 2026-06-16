"use client"

import React, { useState, useEffect, useCallback, useRef } from 'react'
import { Search, Calendar, Mail, MessageCircle, Users, Zap, BarChart3, FileText, Settings, User } from 'lucide-react'
import {
  Dialog,
  DialogContent,
} from './dialog'
import { Input } from './input'

export interface CommandItem {
  id: string
  label: string
  description?: string
  icon: React.ReactNode
  category: 'actions' | 'navigation' | 'settings'
  shortcut?: string
  onSelect: () => void
}

interface CommandPaletteProps {
  isOpen: boolean
  onClose: () => void
  commands: CommandItem[]
  placeholder?: string
}

export function CommandPalette({
  isOpen,
  onClose,
  commands,
  placeholder = "Buscar ação ou digitar comando..."
}: CommandPaletteProps) {
  const [query, setQuery] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(0)
  const inputRef = useRef<HTMLInputElement>(null)

  const filteredCommands = commands.filter(cmd =>
    cmd.label.toLowerCase().includes(query.toLowerCase()) ||
    cmd.description?.toLowerCase().includes(query.toLowerCase())
  )

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!isOpen) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex(prev => {
          if (filteredCommands.length === 0) return 0
          return Math.min(prev + 1, filteredCommands.length - 1)
        })
        break
      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex(prev => Math.max(prev - 1, 0))
        break
      case 'Enter':
        e.preventDefault()
        // Guard: only invoke if filteredCommands exists and has items
        if (filteredCommands.length > 0 && filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].onSelect()
          onClose()
        }
        break
      case 'Escape':
        e.preventDefault()
        onClose()
        break
    }
  }, [isOpen, filteredCommands, selectedIndex, onClose])

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [handleKeyDown])

  useEffect(() => {
    if (!isOpen) {
      setQuery('')
      setSelectedIndex(0)
    } else {
      // Auto-focus on open for keyboard-first flow
      setTimeout(() => {
        inputRef.current?.focus()
      }, 100)
    }
  }, [isOpen])

  const getCategoryLabel = (category: CommandItem['category']) => {
    switch (category) {
      case 'actions': return 'Ações'
      case 'navigation': return 'Navegação'
      case 'settings': return 'Configurações'
    }
  }

  const groupedCommands = filteredCommands.reduce((acc, cmd) => {
    if (!acc[cmd.category]) acc[cmd.category] = []
    acc[cmd.category].push(cmd)
    return acc
  }, {} as Record<string, CommandItem[]>)

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent 
        className="max-w-2xl p-0 gap-0 overflow-hidden bg-lia-bg-secondary"
      >
        <div className="flex items-center px-4 py-3">
          <Search className="w-4 h-4 mr-3 text-lia-text-secondary" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="border-0 focus-visible:ring-0 text-base bg-transparent text-lia-text-primary"
            autoFocus
          />
          <kbd className="ml-2 px-2 py-1 text-xs rounded-xl bg-lia-bg-primary text-lia-text-secondary border border-lia-border-default">
            ESC
          </kbd>
        </div>

        <div className="max-h-content-lg overflow-y-auto">
          {Object.entries(groupedCommands).map(([category, items]) => (
            <div key={category}>
              <div className="px-4 py-2 text-xs font-semibold text-lia-text-tertiary">
                {getCategoryLabel(category as CommandItem['category'])}
              </div>
              {items.map((cmd, index) => {
                const globalIndex = filteredCommands.indexOf(cmd)
                const isSelected = globalIndex === selectedIndex
                
                return (
                  <button
                    key={cmd.id}
                    onClick={() => {
                      cmd.onSelect()
                      onClose()
                    }}
                    onMouseEnter={() => setSelectedIndex(globalIndex)}
                    className={`w-full px-4 py-3 flex items-center gap-3 transition-colors motion-reduce:transition-none text-left text-lia-text-primary ${isSelected ? 'bg-lia-interactive-hover' : 'bg-transparent'}`}
                  >
                    <span className="text-lia-text-secondary flex-shrink-0">
                      {cmd.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{cmd.label}</div>
                      {cmd.description && (
                        <div className="text-sm text-lia-text-tertiary">
                          {cmd.description}
                        </div>
                      )}
                    </div>
                    {cmd.shortcut && (
                      <kbd className="px-2 py-1 text-xs rounded-xl flex-shrink-0 bg-lia-bg-primary text-lia-text-secondary border border-lia-border-default">
                        {cmd.shortcut}
                      </kbd>
                    )}
                  </button>
                )
              })}
            </div>
          ))}

          {filteredCommands.length === 0 && (
            <div className="px-4 py-8 text-center text-lia-text-disabled">
              Nenhum comando encontrado para "{query}"
            </div>
          )}
        </div>

        <div className="px-4 py-2 border-t border-lia-border-default text-xs flex items-center justify-between text-lia-text-secondary">
          <span>Use ↑↓ para navegar, Enter para selecionar</span>
          <span>ESC para fechar</span>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export const defaultCommands = (handlers: {
  onSchedule?: () => void
  onEvaluate?: () => void
  onEmail?: () => void
  onWhatsApp?: () => void
  onCompare?: () => void
  onAnalytics?: () => void
  onSettings?: () => void
  onProfile?: () => void
}): CommandItem[] => [
  {
    id: 'schedule',
    label: 'Agendar Entrevista',
    description: 'Criar novo agendamento via LIA',
    icon: <Calendar className="w-4 h-4" />,
    category: 'actions',
    shortcut: 'A',
    onSelect: handlers.onSchedule || (() => {})
  },
  {
    id: 'evaluate',
    label: 'Avaliar Candidato',
    description: 'Análise de fit técnico via IA',
    icon: <Zap className="w-4 h-4" />,
    category: 'actions',
    shortcut: 'E',
    onSelect: handlers.onEvaluate || (() => {})
  },
  {
    id: 'email',
    label: 'Gerar Email',
    description: 'Email personalizado com LIA',
    icon: <Mail className="w-4 h-4" />,
    category: 'actions',
    onSelect: handlers.onEmail || (() => {})
  },
  {
    id: 'whatsapp',
    label: 'Enviar WhatsApp',
    description: 'Mensagem via WhatsApp Business',
    icon: <MessageCircle className="w-4 h-4" />,
    category: 'actions',
    onSelect: handlers.onWhatsApp || (() => {})
  },
  {
    id: 'compare',
    label: 'Comparar Perfis',
    description: 'Análise comparativa de candidatos',
    icon: <Users className="w-4 h-4" />,
    category: 'actions',
    onSelect: handlers.onCompare || (() => {})
  },
  {
    id: 'analytics',
    label: 'Ver Analytics',
    description: 'Dashboard de métricas',
    icon: <BarChart3 className="w-4 h-4" />,
    category: 'navigation',
    onSelect: handlers.onAnalytics || (() => {})
  },
  {
    id: 'settings',
    label: 'Configurações',
    description: 'Ajustes da plataforma',
    icon: <Settings className="w-4 h-4" />,
    category: 'settings',
    onSelect: handlers.onSettings || (() => {})
  },
  {
    id: 'profile',
    label: 'Meu Perfil',
    description: 'Gerenciar conta e preferências',
    icon: <User className="w-4 h-4" />,
    category: 'settings',
    onSelect: handlers.onProfile || (() => {})
  }
]
