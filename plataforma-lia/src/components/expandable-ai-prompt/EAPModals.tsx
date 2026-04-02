"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
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
import {
  X, Trash2, Check, Loader2, Zap, Globe,
} from "lucide-react"
import { AdvancedFiltersModal, type SearchFilters } from "@/components/search/advanced-filters-modal"
import { TemplateSuggestionToast } from "@/components/template-suggestion-toast"
import { SaveArchetypeModal } from "@/components/search/save-archetype-modal"
import type { SearchSpec } from "@/lib/api/candidate-search"

interface ArchetypeData {
  id: string
  name: string
  description?: string
  department?: string
  hired_candidate?: { name: string }
  criteria?: Record<string, unknown>
}

interface EAPModalsProps {
  // Template suggestion toast
  suggestionQueue: {
    currentSuggestion: unknown
    clearCurrentSuggestion: () => void
  }
  templateSuggestions: {
    dismissSuggestion: (id: string) => void
    updateSettings: (s: { enabled: boolean }) => void
  }
  // Advanced filters modal
  showAdvancedFiltersModal: boolean
  setShowAdvancedFiltersModal: (v: boolean) => void
  advancedFilters: SearchFilters
  setAdvancedFilters: (f: SearchFilters) => void
  onCommand: (command: string, action: string) => void
  // Edit archetype modal
  editingArchetype: ArchetypeData | null
  closeEditArchetype: () => void
  editArchetypeEmoji: string
  setEditArchetypeEmoji: (v: string) => void
  editArchetypeName: string
  setEditArchetypeName: (v: string) => void
  editArchetypeQuery: string
  setEditArchetypeQuery: (v: string) => void
  editArchetypeDescription: string
  setEditArchetypeDescription: (v: string) => void
  editArchetypeTags: string[]
  setEditArchetypeTags: (fn: (prev: string[]) => string[]) => void
  newTagInput: string
  setNewTagInput: (v: string) => void
  saveArchetype: () => void
  isSavingArchetype: boolean
  // Delete archetype dialog
  showDeleteArchetypeDialog: boolean
  setShowDeleteArchetypeDialog: (v: boolean) => void
  archetypeToDelete: ArchetypeData | null
  setArchetypeToDelete: (v: ArchetypeData | null) => void
  confirmDeleteArchetype: () => void
  // Source change modal
  showSourceChangeModal: boolean
  setShowSourceChangeModal: (v: boolean) => void
  pendingSourceChange: string | null
  setPendingSourceChange: (v: string | null) => void
  confirmSourceChange: () => void
  // Save archetype modal
  showSaveArchetypeModal: boolean
  setShowSaveArchetypeModal: (v: boolean) => void
  buildSearchSpecFromEntities: SearchSpec
  naturalSearchValue: string
  handleArchetypeSaved: () => void
}

export function EAPModals({
  suggestionQueue,
  templateSuggestions,
  showAdvancedFiltersModal,
  setShowAdvancedFiltersModal,
  advancedFilters,
  setAdvancedFilters,
  onCommand,
  editingArchetype,
  closeEditArchetype,
  editArchetypeEmoji,
  setEditArchetypeEmoji,
  editArchetypeName,
  setEditArchetypeName,
  editArchetypeQuery,
  setEditArchetypeQuery,
  editArchetypeDescription,
  setEditArchetypeDescription,
  editArchetypeTags,
  setEditArchetypeTags,
  newTagInput,
  setNewTagInput,
  saveArchetype,
  isSavingArchetype,
  showDeleteArchetypeDialog,
  setShowDeleteArchetypeDialog,
  archetypeToDelete,
  setArchetypeToDelete,
  confirmDeleteArchetype,
  showSourceChangeModal,
  setShowSourceChangeModal,
  pendingSourceChange,
  setPendingSourceChange,
  confirmSourceChange,
  showSaveArchetypeModal,
  setShowSaveArchetypeModal,
  buildSearchSpecFromEntities,
  naturalSearchValue,
  handleArchetypeSaved,
}: EAPModalsProps) {
  return (
    <>
      {/* Toast de Sugestão de Template */}
      <TemplateSuggestionToast
        // @ts-ignore TODO: fix type — Type 'unknown' is not assignable to type 'TemplateSuggestion | null'.
        suggestion={suggestionQueue.currentSuggestion}
        onCreateTemplate={(suggestion) => {
          const templateData = {
            name: `Template: ${suggestion.command.substring(0, 30)}...`,
            command: suggestion.command,
            complexity: suggestion.complexity,
            estimatedTime: suggestion.estimatedTime
          }
          sessionStorage.setItem('lia-create-template', JSON.stringify(templateData))
          window.location.href = '/?page=templates'
          suggestionQueue.clearCurrentSuggestion()
        }}
        onDismiss={(suggestionId) => {
          templateSuggestions.dismissSuggestion(suggestionId)
          suggestionQueue.clearCurrentSuggestion()
        }}
        onNotAskAgain={() => {
          templateSuggestions.updateSettings({ enabled: false })
          suggestionQueue.clearCurrentSuggestion()
        }}
      />

      {/* Modal de Filtros Avançados */}
      <AdvancedFiltersModal
        isOpen={showAdvancedFiltersModal}
        onClose={() => setShowAdvancedFiltersModal(false)}
        initialFilters={advancedFilters}
        onApply={(filters) => {
          setAdvancedFilters(filters)
          setShowAdvancedFiltersModal(false)
          onCommand(JSON.stringify(filters), 'apply_filters')
        }}
      />

      {/* Modal de Edição de Arquétipo */}
      {editingArchetype && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
          onClick={closeEditArchetype}
        >
          <div
            className="bg-lia-bg-primary rounded-md p-5 w-full max-w-md mx-4 border border-lia-border-subtle"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold" style={{color: "var(--gray-950)"}}>
                Editar Arquétipo
              </h3>
              <button
                onClick={closeEditArchetype}
                className="p-1.5 rounded-md hover:bg-gray-100 transition-colors motion-reduce:transition-none"
              >
                <X className="w-4 h-4" style={{color: "var(--gray-400)"}} />
              </button>
            </div>

            <div className="space-y-3">
              <div className="flex gap-2">
                <div className="w-16">
                  <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Emoji</label>
                  <input
                    type="text"
                    value={editArchetypeEmoji}
                    onChange={(e) => setEditArchetypeEmoji(e.target.value)}
                    maxLength={4}
                    className="w-full rounded-md px-2 py-2 text-center text-lg focus:outline-none focus:ring-2 focus:ring-gray-400 border border-lia-border-subtle"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Nome</label>
                  <input
                    type="text"
                    value={editArchetypeName}
                    onChange={(e) => setEditArchetypeName(e.target.value)}
                    placeholder="Nome do arquétipo"
                    className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 border border-lia-border-subtle"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Query de Busca</label>
                <textarea
                  value={editArchetypeQuery}
                  onChange={(e) => setEditArchetypeQuery(e.target.value)}
                  placeholder="Ex: Desenvolvedor Python Sênior São Paulo"
                  rows={2}
                  className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none border border-lia-border-subtle"
                />
              </div>

              <div>
                <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Descrição (opcional)</label>
                <textarea
                  value={editArchetypeDescription}
                  onChange={(e) => setEditArchetypeDescription(e.target.value)}
                  placeholder="Breve descrição do perfil ideal..."
                  rows={2}
                  className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 resize-none border border-lia-border-subtle"
                />
              </div>

              <div>
                <label className="text-xs font-medium mb-1 block" style={{color: "var(--gray-400)"}}>Tags</label>
                {editArchetypeTags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-2">
                    {editArchetypeTags.map((tag, index) => (
                      <Badge
                        key={`tag-${index}`}
                        variant="secondary"
                        className="text-xs bg-gray-100 text-lia-text-primary pr-1 flex items-center gap-1"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => setEditArchetypeTags(prev => prev.filter((_, i) => i !== index))}
                          className="ml-0.5 rounded-full hover:bg-gray-200 p-0.5 transition-colors motion-reduce:transition-none"
                        >
                          <X className="w-2.5 h-2.5" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
                <div className="relative">
                  <input
                    type="text"
                    value={newTagInput}
                    onChange={(e) => setNewTagInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && newTagInput.trim()) {
                        e.preventDefault()
                        if (!editArchetypeTags.includes(newTagInput.trim())) {
                          setEditArchetypeTags(prev => [...prev, newTagInput.trim()])
                        }
                        setNewTagInput("")
                      }
                    }}
                    placeholder="Digite e pressione Enter para adicionar..."
                    className="w-full rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-gray-400 border border-lia-border-subtle"
                  />
                  <span className="absolute right-3 top-1/2 -translate-y-1/2 text-micro lia-text-secondary">
                    Enter ↵
                  </span>
                </div>
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <Button
                onClick={closeEditArchetype}
                variant="outline"
                className="flex-1"
                style={{color: "var(--gray-400)"}}
              >
                Cancelar
              </Button>
              <Button
                onClick={saveArchetype}
                disabled={isSavingArchetype || !editArchetypeName}
                className="flex-1"
                style={{
                  backgroundColor: editArchetypeName ? "var(--gray-950)" : "var(--gray-200)",
                  color: editArchetypeName ? "white" : "var(--gray-400)",
                }}
              >
                {isSavingArchetype ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-1.5 animate-spin motion-reduce:animate-none" />
                    Salvando...
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 mr-1.5" />
                    Salvar
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmação para Exclusão de Arquétipo */}
      <AlertDialog open={showDeleteArchetypeDialog} onOpenChange={setShowDeleteArchetypeDialog}>
        <AlertDialogContent
          className="sm:max-w-[320px] w-[85vw] fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-4 rounded-md border"
          style={{backgroundColor: 'var(--gray-50)'}}
        >
          <AlertDialogHeader>
            <AlertDialogTitle className="text-base font-semibold text-lia-text-primary flex items-center gap-2">
              <Trash2 className="w-4 h-4 text-status-error" />
              Excluir Arquétipo
            </AlertDialogTitle>
            <AlertDialogDescription className="text-sm text-lia-text-secondary">
              Tem certeza que deseja excluir o arquétipo{' '}
              <span className="font-medium text-lia-text-primary">"{archetypeToDelete?.name}"</span>?
              <br />
              <span className="text-xs lia-text-secondary mt-1 block">
                Esta ação não pode ser desfeita.
              </span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="gap-2 mt-4">
            <AlertDialogCancel
              onClick={() => {
                setShowDeleteArchetypeDialog(false)
                setArchetypeToDelete(null)
              }}
              className="flex-1 h-9 text-sm px-3 rounded-md bg-lia-bg-primary border border-lia-border-subtle text-lia-text-secondary hover:bg-gray-50"
            >
              Cancelar
            </AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDeleteArchetype}
              className="flex-1 h-9 text-sm px-3 rounded-md text-white flex items-center justify-center gap-1.5"
              style={{backgroundColor: 'var(--status-error)'}}
            >
              <Trash2 className="w-3.5 h-3.5" />
              Excluir
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Modal de Confirmação para Mudança de Fonte (Híbrido/Global) */}
      <AlertDialog open={showSourceChangeModal} onOpenChange={setShowSourceChangeModal}>
        <AlertDialogContent
          className="sm:max-w-sidebar-content w-[80vw] fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 p-3 rounded-md border"
          style={{backgroundColor: 'var(--gray-100)'}}
        >
          <div className="space-y-2 text-xs leading-snug">
            <div className="flex items-center gap-1.5">
              {pendingSourceChange === 'hybrid' ? (
                <Zap className="w-3 h-3 text-lia-text-secondary" />
              ) : (
                <Globe className="w-3 h-3 text-status-warning" />
              )}
              <h3 className="font-semibold text-xs text-lia-text-primary">
                {pendingSourceChange === 'hybrid' ? 'Busca Híbrida' : 'Busca Global'}
              </h3>
            </div>

            <p className="text-micro lia-text-secondary">
              {pendingSourceChange === 'hybrid'
                ? 'Combina base local + global (800M+ perfis).'
                : 'Acessa 800M+ perfis profissionais.'}
            </p>

            <div className="bg-lia-bg-primary rounded-md p-2 space-y-1 border border-lia-border-subtle">
              {pendingSourceChange === 'hybrid' && (
                <div className="flex justify-between text-micro">
                  <span className="text-lia-text-secondary">Local:</span>
                  <span className="font-medium text-wedo-green-light">Grátis</span>
                </div>
              )}
              <div className="flex justify-between text-micro">
                <span className="text-lia-text-secondary">Global:</span>
                <span className="font-medium text-status-warning" aria-live="polite" aria-atomic="true">1 cr/candidato</span>
              </div>
              <div className="flex justify-between text-micro pt-1 border-t border-lia-border-subtle">
                <span className="font-medium text-lia-text-primary">Total estimado:</span>
                <span className="font-semibold text-status-warning" aria-live="polite" aria-atomic="true">1 cr/candidato</span>
              </div>
            </div>

            <div className="flex gap-1.5 pt-1">
              <button
                onClick={() => {
                  setShowSourceChangeModal(false)
                  setPendingSourceChange(null)
                }}
                className="flex-1 h-6 text-micro px-2 rounded-full bg-lia-bg-primary border border-lia-border-subtle text-lia-text-secondary hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={confirmSourceChange}
                className="flex-1 h-6 text-micro px-2 rounded-full text-white flex items-center justify-center gap-1 bg-gray-900"
              >
                {pendingSourceChange === 'hybrid' ? (
                  <>
                    <Zap className="w-2.5 h-2.5" />
                    Ativar
                  </>
                ) : (
                  <>
                    <Globe className="w-2.5 h-2.5" />
                    Ativar
                  </>
                )}
              </button>
            </div>
          </div>
        </AlertDialogContent>
      </AlertDialog>

      {/* Save Archetype Modal */}
      <SaveArchetypeModal
        open={showSaveArchetypeModal}
        onClose={() => setShowSaveArchetypeModal(false)}
        searchSpec={buildSearchSpecFromEntities}
        query={naturalSearchValue}
        onSuccess={handleArchetypeSaved}
      />
    </>
  )
}
