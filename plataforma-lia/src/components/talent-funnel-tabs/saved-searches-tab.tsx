"use client"

import { useLiaModalTracking } from '@/lib/use-lia-modal-tracking'
import { useState } from"react"
import { formatRelativeTime } from"@/lib/format-utils"
import { Button } from"@/components/ui/button"
import { Card, CardContent } from"@/components/ui/card"
import { Chip } from "@/components/ui/chip"
import { Input } from"@/components/ui/input"
import { Textarea } from"@/components/ui/textarea"
import { LIAIcon } from"@/components/ui/lia-icon"
import {
  Bookmark, Play, Edit, Trash2, Plus, Star, X, Check,
  Users, TrendingUp, Clock, Search, Brain, Database,
  Cloud, FileText, Binary, Target, Calendar, AlertCircle,
  MoreHorizontal
} from"lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from"@/components/ui/dialog"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from"@/components/ui/dropdown-menu"
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
import type { SavedSearch, SearchMode, SearchSource } from"@/hooks/candidates/use-talent-funnel"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'

interface SavedSearchesTabProps {
  savedSearches: SavedSearch[]
  onExecuteSearch: (search: SavedSearch) => void
  onAddSearch: (search: Omit<SavedSearch, 'id' | 'createdAt' | 'updatedAt' | 'usageCount' | 'isFavorite'>) => void
  onUpdateSearch: (id: string, updates: Partial<SavedSearch>) => void
  onDeleteSearch: (id: string) => void
  onToggleFavorite: (id: string) => void
  onNavigateToSearch?: () => void
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
    case 'natural': return 'Natural'
    case 'similar': return 'Similar'
    case 'jd': return 'JD'
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
    case 'global': return 'Global'
    case 'hybrid': return 'Híbrido'
    default: return 'Busca'
  }
}


export function SavedSearchesTab({
  savedSearches,
  onExecuteSearch,
  onAddSearch,
  onUpdateSearch,
  onDeleteSearch,
  onToggleFavorite,
  onNavigateToSearch
}: SavedSearchesTabProps) {
  const [searchFilter, setSearchFilter] = useState('')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showEditModal, setShowEditModal] = useState(false)
  // P0-2 (2026-06-18): LIA screen awareness
  useLiaModalTracking('saved-search-create', showCreateModal)
  useLiaModalTracking('saved-search-edit', showEditModal)
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [selectedSearch, setSelectedSearch] = useState<SavedSearch | null>(null)
  const [newSearchName, setNewSearchName] = useState('')
  const [newSearchDescription, setNewSearchDescription] = useState('')
  const [newSearchQuery, setNewSearchQuery] = useState('')
  const [newSearchMode, setNewSearchMode] = useState<SearchMode>('natural')
  const [newSearchSource, setNewSearchSource] = useState<SearchSource>('hybrid')

  const filteredSearches = savedSearches.filter(search => {
    if (!searchFilter) return true
    const term = searchFilter.toLowerCase()
    return (
      search.name.toLowerCase().includes(term) ||
      search.description?.toLowerCase().includes(term) ||
      search.query.toLowerCase().includes(term)
    )
  })

  const favoriteSearches = filteredSearches.filter(s => s.isFavorite)
  const regularSearches = filteredSearches.filter(s => !s.isFavorite)
  const totalUsage = savedSearches.reduce((sum, s) => sum + s.usageCount, 0)

  const handleCreateSearch = () => {
    if (!newSearchName.trim() || !newSearchQuery.trim()) return

    onAddSearch({
      name: newSearchName.trim(),
      description: newSearchDescription.trim() || undefined,
      query: newSearchQuery.trim(),
      mode: newSearchMode,
      source: newSearchSource
    })

    setShowCreateModal(false)
    setNewSearchName('')
    setNewSearchDescription('')
    setNewSearchQuery('')
    setNewSearchMode('natural')
    setNewSearchSource('hybrid')
  }

  const handleEditSearch = () => {
    if (!selectedSearch || !newSearchName.trim()) return

    onUpdateSearch(selectedSearch.id, {
      name: newSearchName.trim(),
      description: newSearchDescription.trim() || undefined,
      query: newSearchQuery.trim()
    })

    setShowEditModal(false)
    setSelectedSearch(null)
  }

  const handleDeleteSearch = () => {
    if (!selectedSearch) return
    onDeleteSearch(selectedSearch.id)
    setShowDeleteConfirm(false)
    setSelectedSearch(null)
  }

  const openEditModal = (search: SavedSearch) => {
    setSelectedSearch(search)
    setNewSearchName(search.name)
    setNewSearchDescription(search.description || '')
    setNewSearchQuery(search.query)
    setNewSearchMode(search.mode)
    setNewSearchSource(search.source)
    setShowEditModal(true)
  }

  const openDeleteConfirm = (search: SavedSearch) => {
    setSelectedSearch(search)
    setShowDeleteConfirm(true)
  }

  const SearchCard = ({ search }: { search: SavedSearch }) => {
    const ModeIcon = getModeIcon(search.mode)
    const SourceIcon = getSourceIcon(search.source)
    const isAIMode = search.mode === 'natural' || search.mode === 'similar'

    return (
      <Card className="group transition-colors motion-reduce:transition-none border-lia-border-subtle dark:border-lia-border-subtle hover:border-lia-border-medium dark:hover:border-lia-border-medium">
        <CardContent className="p-4">
          <div className="flex items-start gap-4">
            <div 
              className={`flex-shrink-0 w-10 h-10 rounded-md flex items-center justify-center ${
 isAIMode ? 'bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle' : 'bg-lia-bg-tertiary dark:bg-lia-bg-secondary'
 }`}
            >
 <ModeIcon className={`w-5 h-5 ${isAIMode ? 'text-lia-text-secondary' : 'text-lia-text-secondary'}`} />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-medium text-lia-text-primary truncate">
                  {search.name}
                </h3>
                {search.isFavorite && (
                  <Star className="w-4 h-4 text-wedo-orange fill-current flex-shrink-0" />
                )}
              </div>

              {search.description && (
                <p className="text-sm text-lia-text-primary mb-2 line-clamp-1">
                  {search.description}
                </p>
              )}

              <div className="p-2 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl mb-3">
                <code className="text-xs text-lia-text-secondary line-clamp-2">
                  {search.query}
                </code>
              </div>

              <div className="flex items-center gap-4 text-xs text-lia-text-primary">
                <Chip density="relaxed" variant="neutral" className="h-5 px-1.5">
                  {getModeLabel(search.mode)}
                </Chip>
                <span className="flex items-center gap-1">
                  <SourceIcon className={`w-3 h-3 ${search.source === 'hybrid' ? 'text-lia-text-secondary' : ''}`} />
                  {getSourceLabel(search.source)}
                </span>
                <span className="flex items-center gap-1">
                  <Play className="w-3 h-3" />
                  {search.usageCount} {search.usageCount === 1 ? 'uso' : 'usos'}
                </span>
                {search.avgResults !== undefined && (
                  <span className="flex items-center gap-1">
                    <Users className="w-3 h-3" />
                    ~{search.avgResults} resultados
                  </span>
                )}
                {search.lastUsed && (
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatRelativeTime(search.lastUsed)}
                  </span>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity motion-reduce:transition-none">
              <Button
                size="sm"
                className="h-8 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
                onClick={() => onExecuteSearch(search)}
              >
                <Play className="w-3.5 h-3.5 mr-1" />
                Executar
              </Button>

              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                    <MoreHorizontal className="w-4 h-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => openEditModal(search)}>
                    <Edit className="w-4 h-4 mr-2" />
                    Editar
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => onToggleFavorite(search.id)}>
                    <Star className={`w-4 h-4 mr-2 ${search.isFavorite ? 'fill-current text-wedo-orange' : ''}`} />
                    {search.isFavorite ? 'Remover dos favoritos' : 'Adicionar aos favoritos'}
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem 
                    onClick={() => openDeleteConfirm(search)}
                    className="text-status-error focus:text-status-error"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Excluir
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-lia-text-primary flex items-center gap-2">
            <Bookmark className="w-5 h-5 text-lia-text-secondary" />
            Buscas Salvas
          </h2>
          <p className="text-xs text-lia-text-secondary mt-0.5">
            {savedSearches.length} {savedSearches.length === 1 ? 'busca salva' : 'buscas salvas'} • {totalUsage} {totalUsage === 1 ? 'execução' : 'execuções'} no total
          </p>
        </div>
      </div>

      {savedSearches.length > 3 && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
          <Input
            placeholder="Filtrar buscas salvas..."
            value={searchFilter}
            onChange={(e) => setSearchFilter(e.target.value)}
            className="pl-10"
          />
        </div>
      )}

      {savedSearches.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-lia-bg-tertiary dark:bg-lia-bg-secondary">
                <Bookmark className="w-5 h-5 text-lia-text-secondary" />
              </div>
              <div>
                <p className="text-2xl font-semibold text-lia-text-primary">{savedSearches.length}</p>
                <p className="text-xs text-lia-text-primary">Buscas Salvas</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-md flex items-center justify-center bg-status-success/10 dark:bg-status-success/20">
                <TrendingUp className="w-5 h-5 text-status-success" />
              </div>
              <div>
                <p className="text-2xl font-semibold text-lia-text-primary">{totalUsage}</p>
                <p className="text-xs text-lia-text-primary">Execuções</p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4 flex items-center gap-3">
              <div className="w-10 h-10 rounded-md flex items-center justify-center bg-wedo-orange/10 dark:bg-wedo-orange/10/20">
                <Star className="w-5 h-5 text-wedo-orange" />
              </div>
              <div>
                <p className="text-2xl font-semibold text-lia-text-primary">{favoriteSearches.length}</p>
                <p className="text-xs text-lia-text-primary">Favoritas</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {favoriteSearches.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Star className="w-4 h-4 text-wedo-orange fill-current" />
            <span className="text-sm font-medium text-lia-text-primary">
              Favoritas ({favoriteSearches.length})
            </span>
          </div>
          <div className="space-y-3">
            {favoriteSearches.map(search => (
              <SearchCard key={search.id} search={search} />
            ))}
          </div>
        </div>
      )}

      {regularSearches.length > 0 && (
        <div className="space-y-3">
          {favoriteSearches.length > 0 && (
            <div className="flex items-center gap-2">
              <Bookmark className="w-4 h-4 text-lia-text-secondary" />
              <span className="text-sm font-medium text-lia-text-primary">
                Outras ({regularSearches.length})
              </span>
            </div>
          )}
          <div className="space-y-3">
            {regularSearches.map(search => (
              <SearchCard key={search.id} search={search} />
            ))}
          </div>
        </div>
      )}

      {savedSearches.length === 0 && (
        <div className="flex flex-col items-center justify-center py-12 text-center bg-[var(--lia-bg-secondary)] dark:bg-lia-bg-primary/50 rounded-xl border border-[var(--lia-border-subtle)]">
          <div className="w-12 h-12 rounded-full flex items-center justify-center mb-3 bg-[var(--lia-bg-tertiary)] dark:bg-lia-bg-secondary">
            <Bookmark className="w-5 h-5 text-lia-text-tertiary" />
          </div>
          <h3 className="text-sm font-medium text-lia-text-primary mb-1">
            Nenhuma busca salva
          </h3>
          <p className="text-xs text-lia-text-tertiary max-w-sm mb-3 leading-relaxed">
            Faça uma busca e clique em"Salvar" para guardar suas pesquisas.
          </p>
          <Button 
            size="sm"
            onClick={() => onNavigateToSearch?.()} 
            className="bg-[var(--lia-btn-primary-bg)] hover:bg-[var(--lia-btn-primary-hover)] text-white text-xs"
          >
            <Search className="w-3.5 h-3.5 mr-1.5" />
            Fazer uma Busca
          </Button>
        </div>
      )}

      {filteredSearches.length === 0 && savedSearches.length > 0 && (
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <AlertCircle className="w-8 h-8 text-lia-text-muted mb-2" />
          <p className="text-xs text-lia-text-tertiary">
            Nenhuma busca encontrada para"{searchFilter}"
          </p>
        </div>
      )}

      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="sm:max-w-panel-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <LIAIcon size="sm" />
              Nova Busca Salva
            </DialogTitle>
            <DialogDescription>
              Crie uma busca personalizada para reutilizar quando precisar
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary">
                Nome da Busca *
              </label>
              <Input
                placeholder="Ex: Devs Frontend Sênior SP"
                value={newSearchName}
                onChange={(e) => setNewSearchName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary">
                Descrição (opcional)
              </label>
              <Input
                placeholder="Breve descrição da busca..."
                value={newSearchDescription}
                onChange={(e) => setNewSearchDescription(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary">
                Query de Busca *
              </label>
              <Textarea
                placeholder="Descreva o perfil que você busca..."
                value={newSearchQuery}
                onChange={(e) => setNewSearchQuery(e.target.value)}
                rows={3}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-lia-text-primary">
                  Modo de Busca
                </label>
                <div className="flex flex-wrap gap-1">
                  {(['natural', 'boolean', 'jd'] as SearchMode[]).map(mode => {
                    const Icon = getModeIcon(mode)
                    return (
                      <Button
                        key={mode}
                        variant={newSearchMode === mode ? 'primary' : 'outline'}
                        size="sm"
                        className={`h-7 text-xs ${newSearchMode === mode ? 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text' : ''}`}
                        onClick={() => setNewSearchMode(mode)}
                      >
                        <Icon className="w-3 h-3 mr-1" />
                        {getModeLabel(mode)}
                      </Button>
                    )
                  })}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-lia-text-primary">
                  Fonte
                </label>
                <div className="flex flex-wrap gap-1">
                  {(['local', 'hybrid', 'global'] as SearchSource[]).map(source => {
                    const Icon = getSourceIcon(source)
                    return (
                      <Button
                        key={source}
                        variant={newSearchSource === source ? 'primary' : 'outline'}
                        size="sm"
                        className={`h-7 text-xs ${newSearchSource === source ? 'bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text' : ''}`}
                        onClick={() => setNewSearchSource(source)}
                      >
                        <Icon className="w-3 h-3 mr-1" />
                        {getSourceLabel(source)}
                      </Button>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleCreateSearch}
              disabled={!newSearchName.trim() || !newSearchQuery.trim()}
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
            >
              <Check className="w-4 h-4 mr-2" />
              Salvar Busca
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
        <DialogContent className="sm:max-w-panel-xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Edit className="w-5 h-5 text-lia-text-secondary" />
              Editar Busca
            </DialogTitle>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary">
                Nome da Busca *
              </label>
              <Input
                value={newSearchName}
                onChange={(e) => setNewSearchName(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary">
                Descrição (opcional)
              </label>
              <Input
                value={newSearchDescription}
                onChange={(e) => setNewSearchDescription(e.target.value)}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-lia-text-primary">
                Query de Busca *
              </label>
              <Textarea
                value={newSearchQuery}
                onChange={(e) => setNewSearchQuery(e.target.value)}
                rows={3}
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowEditModal(false)}>
              Cancelar
            </Button>
            <Button
              onClick={handleEditSearch}
              disabled={!newSearchName.trim()}
              className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
            >
              <Check className="w-4 h-4 mr-2" />
              Salvar Alterações
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir busca salva?</AlertDialogTitle>
            <AlertDialogDescription>
              Tem certeza que deseja excluir"{selectedSearch?.name}"? Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteSearch}
              className="bg-status-error hover:bg-status-error"
            >
              <Trash2 className="w-4 h-4 mr-2" />
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  )
}
