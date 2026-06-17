"use client"

import React from"react"
import Link from"next/link"
import { Chip } from "@/components/ui/chip"
import { LIAIcon } from"@/components/ui/lia-icon"
import { ContextPill } from"@/components/ui/context-pill"
import { QuickActionChips, type QuickAction } from"@/components/ui/quick-action-chips"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from"@/components/ui/tooltip"
import { getCostLevel, getCostColor } from"@/hooks/search/useCreditEstimator"
import {
  Brain, Users, Filter, Zap,
  FileText, Code, Lightbulb, Globe, Home, Coins, AlertCircle, Table2,
} from"lucide-react"
import { EAPTabContent } from './EAPTabContent'

interface EAPExpandedSectionProps {
  contextPill?: { icon: React.ReactNode; primaryText: string; secondaryText: string; onDismiss?: () => void }
  quickActions: Array<{ id: string; label: string; icon?: React.ReactNode; action?: string }>
  searchSource: string
  setSearchSource: (v: 'local' | 'global' | 'hybrid') => void
  handleSourceChange: (v: 'local' | 'hybrid' | 'global') => void
  creditEstimate: { isLocal: boolean; canAfford: boolean; total: number; isLoading: boolean; perCandidate: number; availableCredits?: number }
  pearchSearchType: string
  candidateLimit: number
  filledTagsCount: number
  activeSearchTab: string
  setActiveSearchTab: (v: string) => void
  suggestions: Array<Record<string, unknown>>
  commandHistory: string[]
  showHistory: boolean
  setShowHistory: (v: boolean) => void
  handleHistoryCommand: (cmd: string) => void
  handleSuggestionClick: (s: Record<string, unknown>) => void
  isProcessing: boolean
  isListening: boolean
  lastCommand: string
  core: Record<string, unknown>
}

export function EAPExpandedSection(props: EAPExpandedSectionProps) {
  const {
    contextPill, quickActions, searchSource, setSearchSource, handleSourceChange,
    creditEstimate, pearchSearchType, candidateLimit, filledTagsCount,
    activeSearchTab, setActiveSearchTab,
    suggestions, commandHistory, showHistory, setShowHistory,
    handleHistoryCommand, handleSuggestionClick,
    isProcessing, isListening, lastCommand, core,
  } = props

  return (
    <div className="lia-prompt-expanded space-y-4">

      {(contextPill || quickActions.length > 0) && (
        <div className="p-4 pb-0 border-b border-b-lia-border-subtle">
          {contextPill && (
            <div className="mb-3">
              <ContextPill
                icon={contextPill.icon}
                primaryText={contextPill.primaryText}
                secondaryText={contextPill.secondaryText}
                onDismiss={contextPill.onDismiss}
              />
            </div>
          )}
          
          {quickActions.length > 0 && (
            <div>
              <div className="text-xs mb-2 lia-body">
                Ações rápidas:
              </div>
              <QuickActionChips actions={quickActions as unknown as QuickAction[]} />
            </div>
          )}
        </div>
      )}

      <div className="p-4 pb-0">
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-2">
            <LIAIcon size="sm" />
            <span className="text-sm lia-heading">Pesquisa Avançada</span>
          </div>
          
          <div className="flex items-center gap-3">
            <div className="lia-tabs-container flex items-center gap-1">
              <button
                onClick={() => setSearchSource('local')}
                className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors motion-reduce:transition-none ${
searchSource === 'local' 
                    ? 'lia-tab-active' 
                    : 'lia-tab'
                }`}
                title="Buscar apenas na base local (gratuito)"
              >
                <Home className="w-3 h-3" />
                <span className="hidden sm:inline">Local</span>
              </button>
              <button
                onClick={() => handleSourceChange('hybrid')}
                className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors motion-reduce:transition-none ${
searchSource === 'hybrid' 
                    ? 'lia-tab-active' 
                    : 'lia-tab'
                }`}
                title="Buscar na base local + Base Global (1 cred + $0.01 Apify/cand)"
              >
                <Zap className="w-3 h-3" />
                <span className="hidden sm:inline">Híbrido</span>
              </button>
              <button
                onClick={() => handleSourceChange('global')}
                className={`flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors motion-reduce:transition-none ${
searchSource === 'global' 
                    ? 'lia-tab-active' 
                    : 'lia-tab'
                }`}
                title="Buscar apenas na Base Global (800M+ perfis, 1 cred + $0.01 Apify/cand)"
              >
                <Globe className="w-3 h-3" />
                <span className="hidden sm:inline">Global</span>
              </button>
            </div>
            
            <div className="relative group">
              <div className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-xs ${
creditEstimate.isLocal 
                  ? '' 
                  : !creditEstimate.canAfford
                    ? ''
                    : getCostLevel(creditEstimate.total) === 'low' 
                      ? ''
                      : getCostLevel(creditEstimate.total) === 'medium'
                        ? ''
                        : ''
              }`}>
                <Coins className="w-3 h-3" />
                <span className="font-medium">
                  {creditEstimate.isLoading ? (
                    '...'
                  ) : creditEstimate.isLocal ? (
                    'Gratuito'
                  ) : (
                    `~${creditEstimate.total} créditos`
                  )}
                </span>
                {!creditEstimate.isLocal && !creditEstimate.canAfford && (
                  <AlertCircle className="w-3 h-3 text-status-error" />
                )}
              </div>
              
              <div className="absolute right-0 top-full mt-1.5 hidden group-hover:block z-50">
                <div className="bg-lia-btn-primary-bg text-lia-btn-primary-text px-3 py-2 rounded-md text-xs min-w-[220px]">
                  <div className="font-semibold mb-2 flex items-center gap-1.5">
                    <Coins className="w-3.5 h-3.5 text-status-warning" />
                    Estimativa de Custo
                  </div>
                  {creditEstimate.isLocal ? (
                    <div className="text-status-success">
                      Busca local gratuita - sem custos adicionais
                    </div>
                  ) : (
                    <div className="space-y-1.5">
                      {creditEstimate.availableCredits !== undefined && (
                        <div className="flex justify-between pb-1.5">
                          <span className="lia-text-muted">Saldo disponível:</span>
                          <span className={`font-medium ${
creditEstimate.canAfford ? 'text-status-success' : 'text-status-error'
                          }`}>
                            {creditEstimate.availableCredits} créditos
                          </span>
                        </div>
                      )}
                      <div className="flex justify-between">
                        <span className="lia-text-muted">Tipo de busca:</span>
                        <span className="font-medium">Rápida (1 cred + $0.01 Apify/cand)</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="lia-text-muted" aria-live="polite" aria-atomic="true">Por candidato:</span>
                        <span className="font-medium">{creditEstimate.perCandidate} créditos + $0.01 Apify</span>
                      </div>
                      <div className="flex justify-between pt-1.5 border-t border-lia-border-strong">
                        <span className="lia-text-muted">Total ({candidateLimit} cand.):</span>
                        <span className={`font-bold ${getCostColor(getCostLevel(creditEstimate.total))}`}>
                          {creditEstimate.total} créditos
                        </span>
                      </div>
                      {!creditEstimate.canAfford && (
                        <div className="text-xs text-status-error mt-1.5 pt-1.5 border-t border-lia-border-strong flex items-center gap-1">
                          <AlertCircle className="w-3 h-3" />
                          Saldo insuficiente para esta busca
                        </div>
                      )}
                    </div>
                  )}
                  <div className="absolute bottom-full right-4 border-4 border-transparent border-b-lia-btn-primary-bg"></div>
                </div>
              </div>
            </div>
            
            <span className="text-xs text-lia-text-secondary hidden md:inline">
              {filledTagsCount}/5 critérios
            </span>
          </div>
        </div>
        
        <div className="flex items-center gap-1.5 mb-3 overflow-x-auto pb-1">
          <button
            onClick={() => setActiveSearchTab('natural')}
            className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
activeSearchTab === 'natural' ? 'lia-pill-active' : 'lia-pill'
            }`}
          >
            <Brain className="w-3 h-3 text-wedo-cyan" />
            IA Natural
          </button>
          <button
            onClick={() => setActiveSearchTab('similar')}
            className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
activeSearchTab === 'similar' ? 'lia-pill-active' : 'lia-pill'
            }`}
          >
            <Users className="w-3 h-3" />
            Similar
          </button>
          <button
            onClick={() => setActiveSearchTab('job-description')}
            className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
activeSearchTab === 'job-description' ? 'lia-pill-active' : 'lia-pill'
            }`}
          >
            <FileText className="w-3 h-3" />
            D. Cargo
          </button>
          <button
            onClick={() => setActiveSearchTab('boolean')}
            className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
activeSearchTab === 'boolean' ? 'lia-pill-active' : 'lia-pill'
            }`}
          >
            <Code className="w-3 h-3" />
            Boleana
          </button>
          <button
            onClick={() => setActiveSearchTab('filtros')}
            className={`flex items-center gap-1.5 whitespace-nowrap transition-colors motion-reduce:transition-none ${
activeSearchTab === 'filtros' ? 'lia-pill-active' : 'lia-pill'
            }`}
          >
            <Filter className="w-3 h-3" />
            Filtros
          </button>
          
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Link
                  href="/funil-de-talentos?expandedSearch=true"
                  className="ml-1 p-1.5 rounded-xl hover:bg-lia-bg-tertiary transition-colors motion-reduce:transition-none border border-lia-border-subtle"
                >
                  <Table2 className="w-3.5 h-3.5 text-lia-text-secondary" />
                </Link>
              </TooltipTrigger>
              <TooltipContent side="bottom">
                <p className="text-xs font-medium">Abrir em Tabela</p>
                <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">Ir para resultados de busca</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>

        <div className="mb-3">
          <EAPTabContent {...(core as Parameters<typeof EAPTabContent>[0])} />
        </div>

        <div className="p-2.5 bg-white rounded-xl mb-3 border border-lia-border-subtle">
          <div className="flex items-start gap-2">
            <Lightbulb className="w-3.5 h-3.5 text-lia-text-secondary mt-0.5 flex-shrink-0" />
            <p className="text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
              {activeSearchTab === 'natural' && <><strong>Dica:</strong> Para melhores resultados, seja específico sobre skills, senioridade e localização.</>}
              {activeSearchTab === 'similar' && <><strong>Dica:</strong> Cole o link do LinkedIn de um candidato que você considera ideal.</>}
              {activeSearchTab === 'job-description' && <><strong>Dica:</strong> Cole a descrição do cargo completa para extrair automaticamente requisitos técnicos e comportamentais.</>}
              {activeSearchTab === 'boolean' && <><strong>Dica:</strong> Use aspas para termos exatos e parênteses para agrupar condições.</>}
              {activeSearchTab === 'filtros' && <><strong>Dica:</strong> Combine filtros para refinar sua busca de forma precisa.</>}
              {activeSearchTab === 'arquetipos' && <><strong>Dica:</strong> Use arquétipos para salvar perfis ideais e reutilizar em buscas futuras.</>}
            </p>
          </div>
        </div>
      </div>

      <div className="px-4 pb-0">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <LIAIcon size="sm" />
            <span className="text-sm font-medium text-lia-text-primary">💡 Sugestões Inteligentes</span>
            <Chip density="relaxed" variant="neutral" >
              {suggestions.length} disponíveis
            </Chip>
          </div>

          {commandHistory.length > 0 && (
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="text-xs text-lia-text-secondary hover:text-lia-text-secondary flex items-center gap-1 transition-colors motion-reduce:transition-none"
            >
              📜 Histórico ({commandHistory.length})
            </button>
          )}
        </div>

        {showHistory && commandHistory.length > 0 && (
          <div className="mb-4 p-3 bg-lia-bg-secondary rounded-xl border">
            <h4 className="text-xs font-medium text-lia-text-primary mb-2">Comandos Recentes</h4>
            <div className="space-y-1">
              {commandHistory.map((command, index) => (
                <button
                  key={`hist-${index}`}
                  onClick={() => handleHistoryCommand(command)}
                  disabled={isProcessing}
                  className={`w-full text-left text-xs p-2 rounded-md hover:bg-lia-bg-primary transition-colors motion-reduce:transition-none ${
isProcessing ? 'opacity-50' : 'text-lia-text-secondary hover:text-lia-text-primary'
                  }`}
                >
                  📝 {command}
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {suggestions.map((suggestion) => (
            <button
              key={suggestion.id as string}
              onClick={() => handleSuggestionClick(suggestion)}
              disabled={isProcessing}
              className={`flex items-start gap-3 p-3 text-left rounded-md border border-lia-border-subtle bg-lia-bg-primary transition-colors motion-reduce:transition-none group ${
isProcessing
                  ? 'opacity-50 cursor-not-allowed'
                  : 'hover:border-lia-border-medium hover:'
              }`}
            >
              <span className="text-lg flex-shrink-0">{suggestion.icon as React.ReactNode}</span>
              <div className="flex-1">
                <div className="text-base-ui font-semibold text-lia-text-primary group-hover:text-lia-text-secondary">
                  {suggestion.label as React.ReactNode}
                </div>
                <div className="text-xs text-lia-text-secondary mt-1">
                  {(suggestion.description as React.ReactNode)}
                </div>
                {!!(suggestion.category) && (
                  <Chip variant="neutral" muted className="mt-2 text-micro bg-lia-bg-tertiary text-lia-text-primary border-0">
                    {(suggestion.category as React.ReactNode)}
                  </Chip>
                )}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="px-4 pb-4">
        {isListening && (
          <div className="flex items-center gap-2 text-sm text-status-error bg-status-error/10 p-2 rounded-md mb-3">
            <div className="w-2 h-2 bg-status-error rounded-full animate-pulse motion-reduce:animate-none"></div>
            <span>🎙️ Ouvindo... Fale seu comando</span>
          </div>
        )}

        {isProcessing && (
          <div className="flex items-center gap-2 text-xs text-lia-text-secondary bg-lia-bg-secondary p-2 rounded-xl mb-3 border border-lia-border-subtle">
            <div className="w-2 h-2 bg-lia-btn-primary-bg rounded-full animate-pulse motion-reduce:animate-none"></div>
            <span>🧠 IA processando:"{lastCommand}"</span>
          </div>
        )}

        <div className="text-xs text-lia-text-primary text-center pt-2 space-y-1">
          <div>💡 IA aprende com seus padrões para sugerir ações mais precisas</div>
          <div className="flex justify-center gap-4">
            <span>⌨️ Esc para fechar</span>
            <span>Ctrl+K para focar</span>
            {commandHistory.length > 0 && <span>Ctrl+H para histórico</span>}
          </div>
        </div>
      </div>
    </div>
  )
}
