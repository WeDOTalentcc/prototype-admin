"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState } from"react"
import { formatRelativeTime } from"@/lib/format-utils"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { LIAIcon } from"@/components/ui/lia-icon"
import {
  Search, Clock, Repeat, Bookmark, Trash2, ChevronRight,
  Calendar, Users, Brain, Database, Cloud, FileText,
  Binary, Target, AlertCircle, Check, X, UserX, Loader2
} from"lucide-react"
// Task #403 — recuperar descartados (sem email/telefone) de uma execução
// anterior persistida no backend.
import {
  fetchDiscardedForSearch,
  type DiscardedCandidateDTO,
} from"@/lib/api/candidate-search"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from"@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from"@/components/ui/alert-dialog"
import type { SearchHistoryItem, SearchMode, SearchSource } from"@/hooks/candidates/use-talent-funnel"
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
  // Task #403 — cache local de descartados carregados sob demanda por searchId.
  // 'loading' enquanto a chamada está em voo; null se 404/sem permissão.
  const [discardedCache, setDiscardedCache] = useState<
    Record<string, DiscardedCandidateDTO[] | 'loading' | null>
  >({})

  const handleLoadDiscarded = async (item: SearchHistoryItem, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!item.searchId) return
    // toggle: se já tem dados, esconde; senão, carrega.
    const existing = discardedCache[item.searchId]
    if (Array.isArray(existing)) {
      setDiscardedCache(prev => {
        const next = { ...prev }
        delete next[item.searchId!]
        return next
      })
      return
    }
    if (existing === 'loading') return
    setDiscardedCache(prev => ({ ...prev, [item.searchId!]: 'loading' }))
    const res = await fetchDiscardedForSearch(item.searchId)
    setDiscardedCache(prev => ({
      ...prev,
      [item.searchId!]: res ? res.discarded : null,
    }))
  }

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
      <div className="flex flex-col items-center justify-center py-12 text-center bg-[var(--lia-bg-secondary)] dark:bg-lia-bg-primary/50 rounded-xl border border-[var(--lia-border-subtle)]">
        <div className="w-12 h-12 rounded-full flex items-center justify-center mb-3 bg-[var(--lia-bg-tertiary)] dark:bg-lia-bg-secondary">
          <Clock className="w-5 h-5 text-lia-text-tertiary" />
        </div>
        <h3 className="text-sm font-medium text-lia-text-primary mb-1">
          Nenhuma busca realizada
        </h3>
        <p className="text-xs text-lia-text-tertiary max-w-sm leading-relaxed">
          Suas buscas aparecerão aqui. Faça uma busca para começar.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-lia-text-primary flex items-center gap-2">
            <Clock className="w-5 h-5 text-lia-text-secondary" />
            Histórico de Buscas
          </h2>
          <p className="text-xs text-lia-text-secondary mt-0.5">
            {history.length} {history.length === 1 ? 'busca realizada' : 'buscas realizadas'} • Clique para re-executar
          </p>
        </div>
        <Button 
          variant="ghost" 
          size="sm"
          className="text-xs text-lia-text-primary hover:text-status-error"
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
              <Calendar className="w-4 h-4 text-lia-text-secondary" />
              <span className="text-xs font-medium text-lia-text-primary uppercase tracking-wide">
                {dateGroup}
              </span>
              <div className="flex-1 h-px bg-lia-interactive-active dark:bg-lia-bg-elevated" />
            </div>

            <div className="space-y-2">
              {items.map((item) => {
                const ModeIcon = getModeIcon(item.mode)
                const SourceIcon = getSourceIcon(item.source)
                
                return (
                  <div
                    key={item.id}
                    className="group relative flex items-center gap-4 p-4 rounded-xl border border-lia-border-subtle dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-secondary hover:bg-lia-bg-secondary transition-colors motion-reduce:transition-none cursor-pointer"
                    onClick={() => onReExecuteSearch(item)}
                  >
                    <div 
                      className="flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center bg-transparent"
                    >
                      {item.mode === 'natural' ? (
                        <LIAIcon size="sm" />
                      ) : (
                        <ModeIcon className="w-5 h-5 text-lia-text-secondary" />
                      )}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="text-sm font-medium text-lia-text-primary truncate">"{item.query}"
                        </p>
                      </div>
                      <div className="flex items-center gap-3 text-xs text-lia-text-primary">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatRelativeTime(item.timestamp, { includeTime: true })}
                        </span>
                        <Chip density="relaxed" variant="neutral" className="h-5 px-1.5">
                          {getModeLabel(item.mode)}
                        </Chip>
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
                        {item.searchId && (item.discardedCount ?? 0) > 0 && (
                          <button
                            type="button"
                            onClick={(e) => handleLoadDiscarded(item, e)}
                            className="flex items-center gap-1 text-status-warning hover:underline"
                            title="Ver candidatos descartados (sem email/telefone)"
                          >
                            {discardedCache[item.searchId] === 'loading' ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <UserX className="w-3 h-3" />
                            )}
                            {item.discardedCount} {item.discardedCount === 1 ? 'descartado' : 'descartados'}
                          </button>
                        )}
                      </div>
                      {item.searchId && Array.isArray(discardedCache[item.searchId]) && (
                        <div
                          className="mt-2 rounded-md border border-lia-border-subtle bg-lia-bg-secondary p-2 space-y-1"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <p className="text-xs font-medium text-lia-text-secondary">
                            Descartados nesta busca (sem email/telefone após enriquecimento):
                          </p>
                          {(discardedCache[item.searchId] as DiscardedCandidateDTO[]).length === 0 ? (
                            <p className="text-xs text-lia-text-tertiary">Nenhum descartado registrado.</p>
                          ) : (
                            (discardedCache[item.searchId] as DiscardedCandidateDTO[]).slice(0, 8).map((d) => (
                              <div key={d.id} className="text-xs text-lia-text-primary truncate">
                                <span className="font-medium">{d.name}</span>
                                {d.headline ? ` — ${d.headline}` : ''}
                                {d.linkedin_url && (
                                  <>
                                    {' · '}
                                    <a
                                      href={d.linkedin_url}
                                      target="_blank"
                                      rel="noreferrer"
                                      className="text-lia-text-secondary hover:underline"
                                    >
                                      LinkedIn
                                    </a>
                                  </>
                                )}
                              </div>
                            ))
                          )}
                          {(discardedCache[item.searchId] as DiscardedCandidateDTO[]).length > 8 && (
                            <p className="text-xs text-lia-text-tertiary">
                              +{(discardedCache[item.searchId] as DiscardedCandidateDTO[]).length - 8} outros descartados
                            </p>
                          )}
                        </div>
                      )}
                      {item.searchId && discardedCache[item.searchId] === null && (
                        <p className="mt-1 text-xs text-status-error">Não foi possível carregar os descartados.</p>
                      )}
                    </div>

                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 hover:bg-lia-bg-tertiary"
                        onClick={(e) => handleSaveClick(item, e)}
                        title="Salvar busca"
                      >
                        <Bookmark className="w-4 h-4 text-lia-text-secondary" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 hover:text-status-error hover:bg-status-error/10"
                        onClick={(e) => handleDeleteClick(item.id, e)}
                        title="Remover do histórico"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>

                    <ChevronRight className="w-5 h-5 text-lia-text-tertiary group-hover:text-lia-text-secondary transition-colors motion-reduce:transition-none" />
                  </div>
                )
              })}
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-center gap-2 py-4 text-xs text-lia-text-secondary">
        <LIAIcon size="xs" />
        <span>Clique em qualquer busca para executá-la novamente</span>
      </div>

      <Dialog open={showSaveModal} onOpenChange={setShowSaveModal}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Bookmark className="w-5 h-5 text-lia-text-secondary" />
              Salvar Busca
            </DialogTitle>
            <DialogDescription>
              Salve esta busca para reutilizá-la rapidamente no futuro
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary">
                Nome da Busca *
              </label>
              <Input
                placeholder="Ex: Devs Frontend Sênior SP"
                value={saveName}
                onChange={(e) => setSaveName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary">
                Descrição (opcional)
              </label>
              <Input
                placeholder="Breve descrição da busca..."
                value={saveDescription}
                onChange={(e) => setSaveDescription(e.target.value)}
              />
            </div>

            {selectedItem && (
              <div className="p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                <p className="text-xs text-lia-text-primary mb-1">Query:</p>
                <code className="text-xs text-lia-text-primary">
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
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
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
              className="bg-status-error hover:bg-status-error"
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
