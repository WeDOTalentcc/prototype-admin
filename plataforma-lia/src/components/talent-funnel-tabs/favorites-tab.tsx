"use client"

import { useState, useMemo, useCallback } from"react"
import { Chip } from "@/components/ui/chip"
import { Button } from"@/components/ui/button"
import { EmptyState } from"@/components/ui/empty-state"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import { Input } from"@/components/ui/input"
import { Textarea } from"@/components/ui/textarea"
import {
  Pin, Star, Search, MapPin,
  BarChart3, X, StickyNote,
  TrendingUp,
  MessageSquareText
} from"lucide-react"
import { useLiaEntitySelection } from "@/hooks/shared/use-lia-entity-selection"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from"@/components/ui/popover"
import { textStyles, buttonStyles, cardStyles, badgeStyles } from '@/lib/design-tokens'
import {
  UnifiedCandidateTable,
  CandidateCell,
  ScoreCell,
  LocationCell,
  CompanyCell,
  PositionCell,
  LinkedInCell,
  SalaryCell,
  NoteCell,
  ActionButtons,
  type TableColumn,
  type TableCandidate,
  type TableSortConfig,
  getColumnDefinition,
  COLUMN_PRESETS
} from"@/components/tables"

interface FavoritesTabProps {
  candidates: TableCandidate[]
  pinnedCandidates: Set<string>
  favoriteCandidates: Set<string>
  favoriteNotes: Map<string, string>
  onTogglePin: (candidateId: string) => void
  onToggleFavorite: (candidateId: string, note?: string) => void
  onCandidateClick: (candidate: TableCandidate) => void
  onLIAClick: (candidate: TableCandidate) => void
  onUpdateFavoriteNote?: (candidateId: string, note: string) => void
}

export function FavoritesTab({
  candidates,
  pinnedCandidates,
  favoriteCandidates,
  favoriteNotes = new Map(),
  onTogglePin,
  onToggleFavorite,
  onCandidateClick,
  onLIAClick,
  onUpdateFavoriteNote
}: FavoritesTabProps) {
  const [filterType, setFilterType] = useState<'all' | 'pinned' | 'starred'>('all')
  const [sortConfig, setSortConfig] = useState<TableSortConfig>({ field: 'score', direction: 'desc' })
  const [searchTerm, setSearchTerm] = useState('')
  const [showNoteModal, setShowNoteModal] = useState(false)
  const [selectedCandidateForNote, setSelectedCandidateForNote] = useState<TableCandidate | null>(null)
  const [noteText, setNoteText] = useState('')
  const [viewingNote, setViewingNote] = useState<{candidate: TableCandidate, note: string} | null>(null)

  const filteredCandidates = useMemo(() => {
    let result = candidates.filter(candidate => {
      if (filterType === 'pinned') return pinnedCandidates.has(candidate.id)
      if (filterType === 'starred') return favoriteCandidates.has(candidate.id)
      return true
    })

    if (searchTerm) {
      const term = searchTerm.toLowerCase()
      result = result.filter(c =>
        c.name?.toLowerCase().includes(term) ||
        c.position?.toLowerCase().includes(term) ||
        c.location?.toLowerCase().includes(term) ||
        c.skills?.some((s: string) => s.toLowerCase().includes(term))
      )
    }

    return result as TableCandidate[]
  }, [candidates, filterType, pinnedCandidates, favoriteCandidates, searchTerm])

  const handleFavoriteClick = useCallback((candidate: TableCandidate) => {
    if (favoriteCandidates.has(candidate.id)) {
      onToggleFavorite(candidate.id)
    } else {
      setSelectedCandidateForNote(candidate)
      setNoteText('')
      setShowNoteModal(true)
    }
  }, [favoriteCandidates, onToggleFavorite])

  const handleSaveFavorite = () => {
    if (selectedCandidateForNote) {
      onToggleFavorite(selectedCandidateForNote.id, noteText)
      setShowNoteModal(false)
      setSelectedCandidateForNote(null)
      setNoteText('')
    }
  }

  const handleViewNote = useCallback((candidate: TableCandidate) => {
    const note = favoriteNotes.get(candidate.id) || ''
    setViewingNote({ candidate, note })
  }, [favoriteNotes])

  const handleUpdateNote = () => {
    if (viewingNote && onUpdateFavoriteNote) {
      onUpdateFavoriteNote(viewingNote.candidate.id, viewingNote.note)
    }
    setViewingNote(null)
  }

  const pinnedCount = Array.from(pinnedCandidates).filter(id => candidates.some(c => c.id === id)).length
  const starredCount = Array.from(favoriteCandidates).filter(id => candidates.some(c => c.id === id)).length

  const columns: TableColumn[] = useMemo(() => {
    const nameCol = getColumnDefinition('name')
    const titleCol = getColumnDefinition('position')
    const companyCol = getColumnDefinition('company')
    const locationCol = getColumnDefinition('location')
    const salaryCol = getColumnDefinition('salary')
    const linkedinCol = getColumnDefinition('linkedin')
    const scoreCol = getColumnDefinition('score')

    return [
      {
        id: 'candidate',
        label: nameCol?.label || 'Candidato',
        sortable: nameCol?.sortable ?? true,
        width: nameCol?.width || 220,
        render: (candidate, _col) => (
          <CandidateCell 
            candidate={candidate} 
            isPinned={pinnedCandidates.has(candidate.id)}
            isFavorite={favoriteCandidates.has(candidate.id)}
          />
        )
      },
      {
        id: 'score',
        label: scoreCol?.label || 'Score',
        sortable: scoreCol?.sortable ?? true,
        width: 80,
        render: (candidate) => (
          <ScoreCell score={candidate.liaAnalysis?.score || candidate.lia_score || candidate.score || 0} />
        )
      },
      {
        id: 'position',
        label: titleCol?.label || 'Cargo',
        sortable: titleCol?.sortable ?? true,
        width: titleCol?.width || 150,
        render: (candidate) => (
          <PositionCell candidate={candidate} />
        )
      },
      {
        id: 'company',
        label: companyCol?.label || 'Empresa',
        sortable: companyCol?.sortable ?? true,
        width: companyCol?.width || 140,
        render: (candidate) => (
          <CompanyCell candidate={candidate} />
        )
      },
      {
        id: 'location',
        label: locationCol?.label || 'Localização',
        sortable: locationCol?.sortable ?? true,
        width: locationCol?.width || 120,
        render: (candidate) => (
          <LocationCell candidate={candidate} />
        )
      },
      {
        id: 'salary',
        label: salaryCol?.label || 'Expectativa',
        sortable: salaryCol?.sortable ?? false,
        width: salaryCol?.width || 100,
        render: (candidate) => (
          <SalaryCell value={candidate.salary?.expected || candidate.desired_salary_max} />
        )
      },
      {
        id: 'note',
        label: 'Nota',
        sortable: false,
        width: 60,
        render: (candidate) => (
          <NoteCell 
            hasNote={!!(favoriteNotes.has(candidate.id) && favoriteNotes.get(candidate.id))}
            onViewNote={() => handleViewNote(candidate)}
          />
        )
      },
      {
        id: 'linkedin',
        label: linkedinCol?.label || 'LinkedIn',
        sortable: false,
        width: linkedinCol?.width || 60,
        render: (candidate) => (
          <LinkedInCell url={candidate.linkedin || candidate.linkedin_url} />
        )
      },
      {
        id: 'actions',
        label: 'Ações',
        sortable: false,
        width: 80,
        align: 'right' as const,
        render: (candidate) => (
          <ActionButtons
            isPinned={pinnedCandidates.has(candidate.id)}
            isFavorite={favoriteCandidates.has(candidate.id)}
            onTogglePin={() => onTogglePin(candidate.id)}
            onToggleFavorite={() => handleFavoriteClick(candidate)}
          />
        )
      }
    ]
  }, [pinnedCandidates, favoriteCandidates, favoriteNotes, onTogglePin, handleFavoriteClick, handleViewNote])

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-4">
          <div>
            <h2 className="text-lg font-semibold text-lia-text-primary flex items-center gap-2">
              <Star className="w-5 h-5 text-wedo-orange" />
              Candidatos Favoritos
            </h2>
            <p className="text-xs text-lia-text-secondary mt-0.5">
              {pinnedCount} {pinnedCount === 1 ? 'fixado' : 'fixados'} • {starredCount} {starredCount === 1 ? 'salvo' : 'salvos'}
            </p>
          </div>

          {filteredCandidates.length > 0 && (
            <Popover>
              <PopoverTrigger asChild>
                <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-lia-bg-tertiary dark:bg-lia-bg-secondary transition-colors motion-reduce:transition-none group">
                  <TrendingUp className="w-3.5 h-3.5 text-lia-text-secondary" />
                  <span className="text-xs font-medium text-lia-text-secondary">Análises</span>
                  <Chip density="relaxed" variant="neutral" muted className="h-4 px-1.5 bg-lia-bg-inverse text-white">
                    {filteredCandidates.length}
                  </Chip>
                </button>
              </PopoverTrigger>
              <PopoverContent 
                className="w-80 p-0" 
                align="start"
                sideOffset={8}
              >
                <div className="bg-lia-bg-tertiary dark:bg-lia-bg-secondary p-4 rounded-xl">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-7 h-7 rounded-xl bg-lia-bg-inverse flex items-center justify-center">
                      <BarChart3 className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm font-semibold text-lia-text-secondary">
                      Insights dos Favoritos
                    </span>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-2 bg-lia-bg-primary/60 dark:bg-lia-bg-elevated/60 rounded-xl">
                      <span className="text-xs text-lia-text-primary">Nota média</span>
                      <span className="text-sm font-bold text-lia-text-secondary">
                        {filteredCandidates.length > 0 
                          ? Math.round(filteredCandidates.reduce((acc, c) => acc + (c.liaAnalysis?.score || c.lia_score || c.score || 0), 0) / filteredCandidates.length)
                          : 0}%
                      </span>
                    </div>

                    <div className="p-2 bg-lia-bg-primary/60 dark:bg-lia-bg-elevated/60 rounded-xl">
                      <span className="text-xs text-lia-text-primary block mb-1.5">Top skills</span>
                      <div className="flex flex-wrap gap-1">
                        {Array.from(new Set(filteredCandidates.flatMap(c => ((c.skills || c.technical_skills || []) as string[]).slice(0, 2)))).slice(0, 4).map((skill, idx) => (
                          <Chip density="relaxed" key={idx} variant="neutral" muted className="bg-lia-interactive-active text-lia-text-secondary dark:bg-lia-bg-elevated">
                            {skill}
                          </Chip>
                        ))}
                      </div>
                    </div>

                    <div className="p-2 bg-lia-bg-primary/60 dark:bg-lia-bg-elevated/60 rounded-xl">
                      <span className="text-xs text-lia-text-primary block mb-1.5">Localizações</span>
                      <div className="flex flex-wrap gap-1">
                        {Array.from(new Set(filteredCandidates.map(c => ((c.location || '') as string).split(',')[0]).filter(Boolean))).slice(0, 3).map((loc, idx) => (
                          <Chip density="relaxed" key={idx} variant="neutral" muted className="dark:bg-status-success/10 dark:text-status-success">
                            <MapPin className="w-2.5 h-2.5 mr-0.5" />
                            {loc}
                          </Chip>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          )}
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
            <Input
              placeholder="Buscar nos favoritos..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-64 h-8 text-xs"
            />
          </div>

          <div className="flex items-center gap-1 bg-lia-bg-tertiary dark:bg-lia-bg-secondary rounded-xl p-1">
            <Button
              variant={filterType === 'all' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setFilterType('all')}
              className="h-6 px-2.5 text-xs"
            >
              Todos ({candidates.length})
            </Button>
            <Button
              variant={filterType === 'pinned' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setFilterType('pinned')}
              className="h-6 px-2.5 text-xs"
            >
              <Pin className="w-3 h-3 mr-1" />
              Fixados
            </Button>
            <Button
              variant={filterType === 'starred' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => setFilterType('starred')}
              className="h-6 px-2.5 text-xs"
            >
              <Star className="w-3 h-3 mr-1" />
              Salvos
            </Button>
          </div>
        </div>
      </div>

      {filteredCandidates.length > 0 ? (
        <>
          <UnifiedCandidateTable
            candidates={filteredCandidates}
            enableVirtualScroll={filteredCandidates.length > 50}
            columns={columns}
            pinnedIds={pinnedCandidates}
            favoriteIds={favoriteCandidates}
            sortConfig={sortConfig}
            onSortChange={setSortConfig}
            onCandidateClick={onCandidateClick}
            onTogglePin={onTogglePin}
            onToggleFavorite={(id) => {
              const candidate = filteredCandidates.find(c => c.id === id)
              if (candidate) handleFavoriteClick(candidate)
            }}
            emptyMessage="Nenhum candidato favorito encontrado"
          />
          <div className="px-4 py-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary border-t border-lia-border-subtle dark:border-lia-border-subtle rounded-b-lg -mt-4">
            <p className="text-sm text-lia-text-primary">
              {filteredCandidates.length} candidato{filteredCandidates.length !== 1 ? 's' : ''} 
              {filterType !== 'all' && ` (${filterType === 'pinned' ? 'fixados' : 'salvos'})`}
            </p>
          </div>
        </>
      ) : (
        <EmptyState
          icon={<Star />}
          title="Nenhum candidato em acompanhamento"
          description={
            filterType === 'pinned'
              ? 'Use o ícone de pin para fixar candidatos importantes.'
              : filterType === 'starred'
              ? 'Use o ícone de estrela para salvar candidatos de interesse.'
              : 'Salve ou fixe candidatos nos resultados de busca para acompanhá-los aqui.'
          }
          className="border border-lia-border-subtle rounded-xl bg-lia-bg-secondary dark:bg-lia-bg-primary/50"
        />
      )}

      {showNoteModal && selectedCandidateForNote && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-[1px] flex items-center justify-center z-50" onClick={() => setShowNoteModal(false)}>
          <div 
            className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle w-full max-w-md mx-4 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 dark:border-lia-border-subtle">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-wedo-orange/15 flex items-center justify-center">
                    <Star className="w-4 h-4 text-wedo-orange" />
                  </div>
                  <h3 className="text-base-ui font-semibold text-lia-text-primary">
                    Adicionar aos Favoritos
                  </h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => setShowNoteModal(false)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="p-4">
              <div className="flex items-center gap-3 mb-4 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={selectedCandidateForNote.avatar || selectedCandidateForNote.avatar_url} />
                  <AvatarFallback className="text-sm font-medium bg-lia-interactive-active text-lia-text-secondary">
                    {selectedCandidateForNote.name?.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-lia-text-primary text-xs">
                    {selectedCandidateForNote.name}
                  </p>
                  <p className="text-xs text-lia-text-tertiary">
                    {selectedCandidateForNote.position}
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-lia-text-secondary">
                  Por que você está salvando este candidato? (opcional)
                </label>
                <Textarea
                  placeholder="Ex: Python sênior com inglês fluente, ótimo fit para vaga de backend..."
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  className="h-24 resize-none text-xs border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium"
                />
                <p className="text-xs text-lia-text-tertiary">
                  Esta nota ajuda você a lembrar por que salvou este candidato.
                </p>
              </div>
            </div>

            <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setShowNoteModal(false)}
                className="border-lia-border-subtle text-xs"
              >
                Cancelar
              </Button>
              <Button
                onClick={handleSaveFavorite}
                className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text text-xs"
              >
                <Star className="w-4 h-4 mr-2" />
                Salvar Favorito
              </Button>
            </div>
          </div>
        </div>
      )}

      {viewingNote && (
        <div className="fixed inset-0 bg-black/30 backdrop-blur-[1px] flex items-center justify-center z-50" onClick={() => setViewingNote(null)}>
          <div 
            className="bg-lia-bg-primary dark:bg-lia-bg-primary rounded-xl border border-lia-border-subtle w-full max-w-md mx-4 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="p-4 dark:border-lia-border-subtle">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-status-warning/15 flex items-center justify-center">
                    <StickyNote className="w-4 h-4 text-status-warning" />
                  </div>
                  <h3 className="text-base-ui font-semibold text-lia-text-primary">
                    Nota do Candidato
                  </h3>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-8 w-8 p-0"
                  onClick={() => setViewingNote(null)}
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="p-4">
              <div className="flex items-center gap-3 mb-4 p-3 bg-lia-bg-secondary dark:bg-lia-bg-secondary rounded-xl">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={viewingNote.candidate.avatar || viewingNote.candidate.avatar_url} />
                  <AvatarFallback className="text-sm font-medium bg-lia-interactive-active text-lia-text-secondary">
                    {viewingNote.candidate.name?.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <div className="flex items-center gap-1.5">
                    <p className="font-medium text-lia-text-primary text-xs">
                      {viewingNote.candidate.name}
                    </p>
                    <button
                      className="opacity-40 hover:opacity-100 transition-opacity shrink-0 p-1 rounded hover:bg-lia-bg-subtle text-lia-primary"
                      title={`Falar com LIA sobre ${viewingNote.candidate.name}`}
                      aria-label={`Conversar com LIA sobre ${viewingNote.candidate.name}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        openEntityChat({ type: 'candidate', id: String(viewingNote.candidate.id), name: viewingNote.candidate.name || '' })
                      }}
                    >
                      <MessageSquareText className="w-[18px] h-[18px]" />
                    </button>
                  </div>
                  <p className="text-xs text-lia-text-tertiary">
                    {viewingNote.candidate.position}
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium text-lia-text-secondary">
                  Sua nota sobre este candidato
                </label>
                <Textarea
                  value={viewingNote.note}
                  onChange={(e) => setViewingNote({ ...viewingNote, note: e.target.value })}
                  className="h-24 resize-none text-xs border-lia-border-subtle focus:ring-1 focus:ring-lia-border-medium"
                  placeholder="Adicione uma nota..."
                />
              </div>
            </div>

            <div className="p-4 border-t border-lia-border-subtle dark:border-lia-border-subtle flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={() => setViewingNote(null)}
                className="border-lia-border-subtle text-xs"
              >
                Fechar
              </Button>
              {onUpdateFavoriteNote && (
                <Button
                  onClick={handleUpdateNote}
                  className="bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text text-xs"
                >
                  <StickyNote className="w-4 h-4 mr-2" />
                  Salvar Alterações
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
