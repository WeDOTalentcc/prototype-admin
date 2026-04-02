"use client"

import { Users, Briefcase, List, Mail, X, Database, Loader2, ClipboardCheck, Star, EyeOff, Share2 } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ContextualActionsBannerProps {
  selectedCount: number
  pearchCount?: number
  onDeselectAll: () => void
  onAddToVacancy: () => void
  onAddToList: () => void
  onShareSearch?: () => void
  onSendMessage: () => void
  onSaveToLocalBase?: () => void
  onWSIScreening?: () => void
  onToggleFavorite?: () => void
  onHide?: () => void
  isSavingToBase?: boolean
  isAddingToList?: boolean
}

export function ContextualActionsBanner({
  selectedCount,
  pearchCount = 0,
  onDeselectAll,
  onAddToVacancy,
  onAddToList,
  onShareSearch,
  onSendMessage,
  onSaveToLocalBase,
  onWSIScreening,
  onToggleFavorite,
  onHide,
  isSavingToBase = false,
  isAddingToList = false,
}: ContextualActionsBannerProps) {
  if (selectedCount === 0) return null

  return (
    <div className="mb-4 p-4 rounded-md bg-white dark:bg-lia-bg-secondary border border-lia-border-subtle dark:border-lia-border-subtle">
      <div className="flex items-center justify-between flex-wrap gap-3">
        {/* Left: Selection info */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-lia-bg-secondary flex items-center justify-center flex-shrink-0">
              <Users className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            </div>
            <span className="text-sm font-semibold text-lia-text-primary" aria-live="polite" aria-atomic="true">
              {selectedCount} candidato{selectedCount > 1 ? 's' : ''} selecionado{selectedCount > 1 ? 's' : ''}
            </span>
          </div>
        </div>

        {/* Center: Action buttons */}
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onAddToVacancy}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary dark:bg-lia-bg-elevated dark:hover:bg-gray-600"
            title="Adicionar à Vaga"
          >
            <Briefcase className="w-3.5 h-3.5 lia-text-base" />
            <span aria-live="polite" aria-atomic="true">Vaga</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onAddToList}
            disabled={isAddingToList}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary dark:bg-lia-bg-elevated dark:hover:bg-gray-600"
            title="Adicionar à Lista"
          >
            {isAddingToList ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none lia-text-secondary" />
            ) : (
              <List className="w-3.5 h-3.5 text-wedo-green" />
            )}
            <span>{isAddingToList ? 'Importando...' : 'Lista'}</span>
          </Button>

          {onShareSearch && (
            <Button
              variant="outline"
              size="sm"
              onClick={onShareSearch}
              className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary dark:bg-lia-bg-elevated dark:hover:bg-gray-600"
              title="Compartilhar Busca"
            >
              <Share2 className="w-3.5 h-3.5 lia-text-base" />
              <span>Compartilhar</span>
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={onSendMessage}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary dark:bg-lia-bg-elevated dark:hover:bg-gray-600"
            title="Enviar Mensagem"
          >
            <Mail className="w-3.5 h-3.5 lia-text-base" />
            <span>Mensagem</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onWSIScreening}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary dark:bg-lia-bg-elevated dark:hover:bg-gray-600"
            title="Triagem WSI"
          >
            <ClipboardCheck className="w-3.5 h-3.5 text-lia-text-secondary dark:text-lia-text-tertiary" />
            <span>Triagem WSI</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onToggleFavorite}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary dark:bg-lia-bg-elevated dark:hover:bg-gray-600"
            title="Adicionar aos Favoritos"
          >
            <Star className="w-3.5 h-3.5 text-wedo-green" />
            <span>Favoritos</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onHide}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary dark:bg-lia-bg-elevated dark:hover:bg-gray-600"
            title="Ocultar Candidatos"
          >
            <EyeOff className="w-3.5 h-3.5 lia-text-secondary" />
            <span>Ocultar</span>
          </Button>

          {pearchCount > 0 && onSaveToLocalBase && (
            <Button
              variant="outline"
              size="sm"
              onClick={onSaveToLocalBase}
              disabled={isSavingToBase}
              className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-lia-border-subtle text-lia-text-primary dark:text-lia-text-primary dark:bg-lia-bg-elevated dark:hover:bg-gray-600"
              title="Salvar na Base Local"
            >
              {isSavingToBase ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin motion-reduce:animate-none lia-text-secondary" />
              ) : (
                <Database className="w-3.5 h-3.5 lia-text-base" />
              )}
              <span>Salvar na Base ({pearchCount})</span>
            </Button>
          )}
        </div>

        {/* Right: Clear button */}
        <Button
          variant="ghost"
          size="sm"
          onClick={onDeselectAll}
          className="h-8 px-2 text-xs text-lia-text-primary hover:text-lia-text-primary dark:text-lia-text-primary dark:hover:text-lia-text-inverse"
          title="Limpar seleção"
        >
          <X className="w-3 h-3" />
        </Button>
      </div>
    </div>
  )
}
