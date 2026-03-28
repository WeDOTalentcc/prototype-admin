"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { LIAIcon } from "@/components/ui/lia-icon"
import {
  Search, Clock, Repeat, Bookmark, Trash2, ChevronRight,
  Calendar, Users, Brain, Database, Cloud, FileText,
  Binary, Target, AlertCircle, Check, X
} from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import type { SearchHistoryItem, SearchMode, SearchSource } from "@/hooks/use-talent-funnel"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

interface HistoryTabProps {
  history: SearchHistoryItem[]
  onReExecuteSearch: (item: SearchHistoryItem) => void
  onSaveAsSearch: (item: SearchHistoryItem, name: string, description?: string) => void
  onDeleteItem: (id: string) => void
  onClearAll: () => void
}

const getModeIcon = (mode: SearchMode) => {
  switch (mode) {
    case 'natural': return Brain
    case 'similar': return Users
    case 'jd': return FileText
    case 'boolean': return Binary
    case 'archetypes': return Target
    default: return Search
  }
}

const getModeLabel = (mode: SearchMode) => {
  switch (mode) {
    case 'natural': return 'Busca Natural'
    case 'similar': return 'Perfil Similar'
    case 'jd': return 'Job Description'
    case 'boolean': return 'Boolean'
    case 'archetypes': return 'Arquétipos'
    default: return 'Busca'
  }
}

const getSourceIcon = (source: SearchSource) => {
  switch (source) {
    case 'local': return Database
    case 'global': return Cloud
    case 'hybrid': return Brain
    default: return Search
  }
}

const getSourceLabel = (source: SearchSource) => {
  switch (source) {
    case 'local': return 'Local'
    case 'global': return 'Base Global'
    case 'hybrid': return 'Híbrido'
    default: return 'Busca'
  }
}

const formatRelativeTime = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Agora'
  if (diffMins < 60) return `Há ${diffMins} min`
  if (diffHours < 24) return `Há ${diffHours}h`
  if (diffDays === 1) return 'Ontem'
  if (diffDays < 7) return `Há ${diffDays} dias`
  
  return date.toLocaleDateString('pt-BR', { 
    day: '2-digit', 
    month: 'short',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const groupByDate = (items: SearchHistoryItem[]) => {
  const groups: { [key: string]: SearchHistoryItem[] } = {}
  
  items.forEach(item => {
    const date = new Date(item.timestamp)
    const today = new Date()
    const yesterday = new Date(today)
    yesterday.setDate(yesterday.getDate() - 1)
    
    let groupKey: string
    
    if (date.toDateString() === today.toDateString()) {
      groupKey = 'Hoje'
    } else if (date.toDateString() === yesterday.toDateString()) {
      groupKey = 'Ontem'
    } else {
      groupKey = date.toLocaleDateString('pt-BR', { 
        weekday: 'long',
        day: 'numeric',
        month: 'long'
      })
    }
    
    if (!groups[groupKey]) {
      groups[groupKey] = []
    }
    groups[groupKey].push(item)
  })
  
  return groups
}

export function HistoryTab({ 
  history,
  onReExecuteSearch, 
  onSaveAsSearch,
  onDeleteItem,
  onClearAll
}: HistoryTabProps) {
  const [showSaveModal, setShowSaveModal] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [selectedItem, setSelectedItem] = useState<SearchHistoryItem | null>(null)
  const [saveName, setSaveName] = useState('')
  const [saveDescription, setSaveDescription] = useState('')

  const groupedHistory = groupByDate(history)

  const handleSaveClick = (item: SearchHistoryItem, e: React.MouseEvent) => {
    e.stopPropagation()
    setSelectedItem(item)
    setSaveName(item.query.substring(0, 50) + (item.query.length > 50 ? '...' : ''))
    setSaveDescription('')
    setShowSaveModal(true)
  }

  const handleSaveSearch = () => {
    if (!selectedItem || !saveName.trim()) return
    onSaveAsSearch(selectedItem, saveName.trim(), saveDescription.trim() || undefined)
    setShowSaveModal(false)
    setSelectedItem(null)
    setSaveName('')
    setSaveDescription('')
  }

  const handleDeleteClick = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    onDeleteItem(id)
  }

  if (history.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center bg-[var(--lia-bg-secondary)] dark:bg-gray-900/50 rounded-md border border-[var(--lia-border-subtle)] dark:border-gray-800">
        <div className="w-12 h-12 rounded-full flex items-center justify-center mb-3 bg-[var(--lia-bg-tertiary)] dark:bg-gray-800">
          <Clock className="w-5 h-5 text-[var(--lia-text-tertiary)]" />
        </div>
        <h3 className="text-sm font-medium text-[var(--lia-text-primary)] dark:text-gray-200 mb-1">
          Nenhuma busca realizada
        </h3>
        <p className="text-xs text-[var(--lia-text-tertiary)] dark:text-gray-500 max-w-sm leading-relaxed">
          Suas buscas aparecerão aqui. Faça uma busca para começar.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-950 dark:text-gray-50 font-['Open_Sans',sans-serif] flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            Histórico de Buscas
          </h2>
          <p className="text-xs text-gray-600 dark:text-gray-400 mt-0.5">
            {history.length} {history.length === 1 ? 'busca realizada' : 'buscas realizadas'} • Clique para re-executar
          </p>
        </div>
        <Button 
          variant="ghost" 
          size="sm"
          className="text-xs text-gray-800 dark:text-gray-200 hover:text-red-600"
          onClick={() => setShowClearConfirm(true)}
        >
          <Trash2 className="w-3.5 h-3.5 mr-1" />
          Limpar Tudo
        </Button>
      </div>

      <div className="space-y-6">
        {Object.entries(groupedHistory).map(([dateGroup, items]) => (
          <div key={dateGroup}>
            <div className="flex items-center gap-2 mb-3">
              <Calendar className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              <span className="text-xs font-medium text-gray-800 dark:text-gray-200 uppercase tracking-wide">
                {dateGroup}
              </span>
              <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700" />
            </div>

            <div className="space-y-2">
              {items.map((item) => {
                const ModeIcon = getModeIcon(item.mode)
                const SourceIcon = getSourceIcon(item.source)
                
                return (
                  <div
                    key={item.id}
                    className="group relative flex items-center gap-4 p-4 rounded-md border border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 hover:bg-gray-50 hover:transition-all cursor-pointer"
                    onClick={() => onReExecuteSearch(item)}
                  >
                    <div 
                      className="flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center bg-transparent"
                    >
                      {item.mode === 'natural' ? (
                        <LIAIcon size="sm" />
                      ) : (
                        <ModeIcon className="w-5 h-5 text-gray-600 dark:text-gray-400" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-medium text-gray-950 dark:text-gray-50 truncate">
                          "{item.query}"
                        </p>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-gray-800 dark:text-gray-200">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatRelativeTime(item.timestamp)}
                        </span>
                        <Badge variant="outline" className="h-5 text-[11px] px-1.5">
                          {getModeLabel(item.mode)}
                        </Badge>
                        <span className="flex items-center gap-1">
                          <SourceIcon className="w-3 h-3" />
                          {getSourceLabel(item.source)}
                        </span>
                        {item.resultsCount !== undefined && (
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {item.resultsCount} {item.resultsCount === 1 ? 'resultado' : 'resultados'}
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 hover:bg-gray-100"
                        onClick={(e) => handleSaveClick(item, e)}
                        title="Salvar busca"
                      >
                        <Bookmark className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 hover:text-red-600 hover:bg-red-50"
                        onClick={(e) => handleDeleteClick(item.id, e)}
                        title="Remover do histórico"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>

                    <ChevronRight className="w-5 h-5 text-gray-300 group-hover:text-gray-600 transition-colors" />
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-2 py-4 text-xs text-gray-600 dark:text-gray-400">
        <LIAIcon size="xs" />
        <span>Clique em qualquer busca para executá-la novamente</span>
      </div>

      <Dialog open={showSaveModal} onOpenChange={setShowSaveModal}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bookmark className="w-5 h-5 text-gray-600 dark:text-gray-400" />
              Salvar Busca
            </DialogTitle>
            <DialogDescription>
              Salve esta busca para reutilizá-la rapidamente no futuro
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200">
                Nome da Busca *
              </label>
              <Input
                placeholder="Ex: Devs Frontend Sênior SP"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-gray-800 dark:text-gray-200">
                Descrição (opcional)
              </label>
              <Input
                placeholder="Breve descrição da busca..."
                value={saveDescription}
                onChange={(e) => setSaveDescription(e.target.value)}
              />
            </div>

            {selectedItem && (
              <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                <p className="text-xs text-gray-800 dark:text-gray-200 mb-1">Query:</p>
                <code className="text-xs text-gray-800 dark:text-gray-200">
                  {selectedItem.query}
                </code>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSaveModal(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleSaveSearch}
              disabled={!saveName.trim()}
              className="bg-[#1a1a1a] hover:bg-[#2a2a2a] text-white"
            >
              <Check className="w-4 h-4 mr-2" />
              Salvar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={showClearConfirm} onOpenChange={setShowClearConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Limpar todo o histórico?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja limpar todo o histórico de buscas? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                onClearAll()
                setShowClearConfirm(false)
              }}
              className="bg-red-600 hover:bg-red-700"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Limpar Tudo
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}

export type { SearchHistoryItem }
