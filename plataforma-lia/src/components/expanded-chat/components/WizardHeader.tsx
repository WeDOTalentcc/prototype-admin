"use client"

import React from "react"
import { FileText, Loader2, Check, Circle, RefreshCw, Minimize2, Maximize2, X, CheckCircle2, AlertCircle, Settings } from "lucide-react"
import { cn } from "@/lib/utils"
import { type ExtendedWizardStageConfig } from "../config"
import { WizardSidebar } from "./WizardSidebar"

export interface CatalogStatus {
  maturity_level: 'complete' | 'partial' | 'minimal' | 'empty'
  message?: string
}

export interface WizardHeaderProps {
  currentStageConfig: ExtendedWizardStageConfig
  currentStageIndex: number
  catalogStatus?: CatalogStatus | null
  isAutoSaving: boolean
  autoSaveLastSaved: Date | null
  hasPendingChanges: boolean
  hasRestoredDraft: boolean
  isFullscreen: boolean
  onFullscreenChange: (isFullscreen: boolean) => void
  onPanelClose: () => void
  onClearDraft: () => void
  getLastSavedText: () => string | null
}

export function WizardHeader({
  currentStageConfig,
  currentStageIndex,
  catalogStatus,
  isAutoSaving,
  autoSaveLastSaved,
  hasPendingChanges,
  hasRestoredDraft,
  isFullscreen,
  onFullscreenChange,
  onPanelClose,
  onClearDraft,
  getLastSavedText
}: WizardHeaderProps) {
  return (
    <div className="px-3 py-2 rounded-t-xl bg-white">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <div className="w-5 h-5 rounded-md flex items-center justify-center bg-gray-900 dark:bg-gray-50">
            <FileText className="w-3 h-3 text-white" />
          </div>
          <span className="text-xs font-semibold text-gray-950">
            {currentStageConfig.panelTitle}
          </span>
          {catalogStatus && (
            <span 
              className={cn(
                "inline-flex items-center gap-1 px-1.5 py-0.5 text-micro font-medium rounded-full",
                catalogStatus.maturity_level === 'complete' 
                  ? "bg-status-success/10 text-status-success"
                  : catalogStatus.maturity_level === 'partial'
                  ? "bg-status-warning/10 text-status-warning"
                  : "bg-gray-100 text-gray-500"
              )}
             
            >
              {catalogStatus.maturity_level === 'complete' ? (
                <>
                  <CheckCircle2 className="w-2.5 h-2.5" />
                  Catálogo Completo
                </>
              ) : catalogStatus.maturity_level === 'partial' ? (
                <>
                  <AlertCircle className="w-2.5 h-2.5" />
                  Catálogo Parcial
                </>
              ) : (
                <>
                  <Settings className="w-2.5 h-2.5" />
                  Configure seu catálogo
                </>
              )}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5">
          <div className="flex items-center gap-1 text-micro">
            {isAutoSaving ? (
              <>
                <Loader2 className="w-3 h-3 text-gray-600 dark:text-gray-400 animate-spin" />
                <span className="text-gray-500">Salvando...</span>
              </>
            ) : autoSaveLastSaved ? (
              <>
                <Check className="w-3 h-3 text-status-success" />
                <span className="text-status-success">{getLastSavedText() || 'Salvo'}</span>
              </>
            ) : hasPendingChanges ? (
              <>
                <Circle className="w-3 h-3 text-status-warning" />
                <span className="text-status-warning">Não salvo</span>
              </>
            ) : null}
          </div>
          {(autoSaveLastSaved || hasRestoredDraft) && (
            <button
              onClick={onClearDraft}
              className="p-1 rounded-md hover:bg-status-error/10 transition-colors group focus-visible:ring-2 focus-visible:ring-gray-400"
              title="Começar do zero"
              aria-label="Limpar rascunho e começar do zero"
            >
              <RefreshCw className="w-3.5 h-3.5 text-gray-400 group-hover:text-status-error transition-colors" />
            </button>
          )}
          <button
            onClick={() => onFullscreenChange(!isFullscreen)}
            className="p-1 rounded-md hover:bg-gray-100 dark:bg-gray-800 transition-colors group focus-visible:ring-2 focus-visible:ring-gray-400"
            title={isFullscreen ? "Reduzir chat" : "Expandir tela cheia"}
            aria-label={isFullscreen ? "Reduzir chat" : "Expandir para tela cheia"}
          >
            {isFullscreen 
              ? <Minimize2 className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors" />
              : <Maximize2 className="w-3.5 h-3.5 text-gray-400 group-hover:text-gray-900 dark:group-hover:text-gray-50 transition-colors" />
            }
          </button>
          <button 
            onClick={onPanelClose}
            className="p-1 rounded-md hover:bg-gray-100 transition-colors focus-visible:ring-2 focus-visible:ring-gray-400"
            title="Fechar painel"
            aria-label="Fechar painel de etapas"
          >
            <X className="w-4 h-4 text-gray-500" />
          </button>
        </div>
      </div>
      
      {catalogStatus && 
        (catalogStatus.maturity_level === 'complete' || 
         catalogStatus.maturity_level === 'partial') && (
        <div 
          className={cn(
            "mt-2 px-2.5 py-1.5 rounded-md flex items-center gap-2 border",
            catalogStatus.maturity_level === 'complete'
              ? "bg-status-success/[0.08] border-status-success/30/20"
              : "bg-status-warning/[0.08] border-status-warning/20"
          )}
        >
          <CheckCircle2 
            className={cn(
              "w-3.5 h-3.5 flex-shrink-0",
              catalogStatus.maturity_level === 'complete'
                ? "text-status-success"
                : "text-status-warning"
            )}
          />
          <span 
            className={cn(
              "text-micro font-medium",
              catalogStatus.maturity_level === 'complete'
                ? "text-status-success"
                : "text-status-warning"
            )}
           
          >
            Políticas da empresa carregadas
          </span>
        </div>
      )}
      
      <div className="mt-2">
        <WizardSidebar 
          currentStageIndex={currentStageIndex}
          orientation="horizontal"
          allowNavigateToCompleted={false}
        />
      </div>
    </div>
  )
}
