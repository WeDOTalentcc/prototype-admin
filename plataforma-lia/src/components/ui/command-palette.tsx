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
        className="max-w-2xl p-0 gap-0 overflow-hidden"
        className="bg-gray-50 dark:bg-gray-900"
      >
        <div className="flex items-center px-4 py-3 border-b" className="border-gray-300 dark:border-gray-600">
          <Search className="w-4 h-4 mr-3 text-gray-600 dark:text-gray-400" />
          <Input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="border-0 focus-visible:ring-0 text-base"
            style={{ 
              backgroundColor: 'transparent',
              color: 'rgb(31 41 55)'
            }}
            autoFocus
          />
          <kbd className="ml-2 px-2 py-1 text-xs rounded" style={{ 
            backgroundColor: 'rgb(255 255 255)',
            color: 'rgb(156 163 175)',
            border: '1px solid rgb(209 213 219)'
          }}>
            ESC
          </kbd>
        </div>

        <div className="max-h-[400px] overflow-y-auto">
          {Object.entries(groupedCommands).map(([category, items]) => (
            <div key={category}>
              <div className="px-4 py-2 text-xs font-semibold" className="text-gray-400 dark:text-gray-500">
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
                    className="w-full px-4 py-3 flex items-center gap-3 transition-colors text-left"
                    style={{
                      backgroundColor: isSelected ? 'rgb(243 244 246)' : 'transparent',
                      color: 'rgb(31 41 55)'
                    }}
                  >
                    <span className="text-gray-600 dark:text-gray-400 flex-shrink-0">
                      {cmd.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{cmd.label}</div>
                      {cmd.description && (
                        <div className="text-sm" className="text-gray-500 dark:text-gray-400">
                          {cmd.description}
                        </div>
                      )}
                    </div>
                    {cmd.shortcut && (
                      <kbd className="px-2 py-1 text-xs rounded flex-shrink-0" style={{ 
                        backgroundColor: 'rgb(255 255 255)',
                        color: 'rgb(156 163 175)',
                        border: '1px solid rgb(209 213 219)'
                      }}>
                        {cmd.shortcut}
                      </kbd>
                    )}
                  </button>
                )
              })}
            </div>
          ))}

          {filteredCommands.length === 0 && (
            <div className="px-4 py-8 text-center" className="text-gray-400 dark:text-gray-500">
              Nenhum comando encontrado para "{query}"
            </div>
          )}
        </div>

        <div className="px-4 py-2 border-t text-xs flex items-center justify-between" style={{ 
          borderColor: 'rgb(209 213 219)',
          color: 'rgb(156 163 175)'
        }}>
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
