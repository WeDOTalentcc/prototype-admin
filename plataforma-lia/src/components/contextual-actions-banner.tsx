"use client"

import { Users, Briefcase, List, Mail, Brain, X, Database, Loader2, ClipboardCheck, Star, EyeOff, Share2 } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ContextualActionsBannerProps {
  selectedCount: number
  pearchCount?: number
  onDeselectAll: () => void
  onAddToVacancy: () => void
  onAddToList: () => void
  onShareSearch?: () => void
  onSendMessage: () => void
  onAnalyze: () => void
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
  onAnalyze,
  onSaveToLocalBase,
  onWSIScreening,
  onToggleFavorite,
  onHide,
  isSavingToBase = false,
  isAddingToList = false,
}: ContextualActionsBannerProps) {
  if (selectedCount === 0) return null

  return (
    <div className="mb-4 p-4 rounded-md bg-gray-50 dark:bg-gray-800 border border-gray-100 dark:border-gray-700">
      <div className="flex items-center justify-between flex-wrap gap-3">
        {/* Left: Selection info */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gray-100 dark:bg-gray-800 flex items-center justify-center flex-shrink-0">
              <Users className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            </div>
            <span className="text-sm font-semibold text-gray-950 dark:text-gray-50">
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
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
            title="Adicionar à Vaga"
          >
            <Briefcase className="w-3.5 h-3.5 text-gray-600" />
            <span>Vaga</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onAddToList}
            disabled={isAddingToList}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
            title="Adicionar à Lista"
          >
            {isAddingToList ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-500" />
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
              className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
              title="Compartilhar Busca"
            >
              <Share2 className="w-3.5 h-3.5 text-gray-600" />
              <span>Compartilhar</span>
            </Button>
          )}

          <Button
            variant="outline"
            size="sm"
            onClick={onSendMessage}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
            title="Enviar Mensagem"
          >
            <Mail className="w-3.5 h-3.5 text-gray-600" />
            <span>Mensagem</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onWSIScreening}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
            title="Triagem WSI"
          >
            <ClipboardCheck className="w-3.5 h-3.5 text-gray-600 dark:text-gray-400" />
            <span>Triagem WSI</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onToggleFavorite}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
            title="Adicionar aos Favoritos"
          >
            <Star className="w-3.5 h-3.5 text-wedo-green" />
            <span>Favoritos</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onHide}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
            title="Ocultar Candidatos"
          >
            <EyeOff className="w-3.5 h-3.5 text-gray-500" />
            <span>Ocultar</span>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onAnalyze}
            className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
            title="Análise LIA"
          >
            <Brain className="w-3.5 h-3.5 text-wedo-cyan" />
            <span>Análise LIA</span>
          </Button>

          {pearchCount > 0 && onSaveToLocalBase && (
            <Button
              variant="outline"
              size="sm"
              onClick={onSaveToLocalBase}
              disabled={isSavingToBase}
              className="h-8 px-3 text-xs gap-1.5 bg-white hover:bg-gray-50 border-gray-200 text-gray-800 dark:text-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600"
              title="Salvar na Base Local"
            >
              {isSavingToBase ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin text-gray-500" />
              ) : (
                <Database className="w-3.5 h-3.5 text-gray-600" />
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
          className="h-8 px-2 text-xs text-gray-800 hover:text-gray-950 dark:text-gray-200 dark:hover:text-gray-50"
          title="Limpar seleção"
        >
          <X className="w-3 h-3" />
        </Button>
      </div>
    </div>
  )
}
