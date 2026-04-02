"use client"

/**
 * SearchCalibrationStage — painel lateral da etapa search-calibration.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.4 — 2026-03-27).
 * Portabilidade Vue: props → defineProps; callbacks → emit.
 */

import { Brain, CheckCircle2, Users, Target, AlertTriangle, RefreshCw, ChevronRight, Eye, Loader2, FileText, BarChart3, Calendar, Bell, Clock, MessageSquare, Rocket, ExternalLink, Database, Globe } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { useExpandedChatContext } from "../ExpandedChatContext"
import type { CalibrationCandidate } from "../types"

interface SearchCalibrationStageProps {
  // Calibration state
  searchPhase: 'idle' | 'local-searching' | 'local-complete' | 'global-searching' | 'global-complete'
  calibrationCandidates: CalibrationCandidate[]
  calibrationComplete: boolean
  isLoadingCalibration: boolean
  hasAttemptedCalibrationGeneration: boolean
  approvedCandidates: string[]
  showCalibrationModal: boolean
  publishedJobId: string | null
  localCandidateCount: number
  globalCandidateCount: number
  globalSearchAuthorized: boolean
  preferredCandidateCount: number
  // Calibration actions
  onSetPreferredCandidateCount: (count: number) => void
  onSetGlobalSearchAuthorized: (authorized: boolean) => void
  onSetSearchPhase: (phase: SearchCalibrationStageProps['searchPhase']) => void
  onSetHasAttemptedCalibrationGeneration: (val: boolean) => void
  onSetCalibrationComplete: (val: boolean) => void
  onSetShowCalibrationModal: (val: boolean) => void
  onGenerateCalibrationCandidates: () => void
  onStartGlobalSearch: () => void
  // Modal navigation
  onJobCreated?: () => void
  onClose: () => void
}

export function SearchCalibrationStage({
  searchPhase,
  calibrationCandidates,
  calibrationComplete,
  isLoadingCalibration,
  hasAttemptedCalibrationGeneration,
  approvedCandidates,
  showCalibrationModal,
  publishedJobId,
  localCandidateCount,
  globalCandidateCount,
  globalSearchAuthorized,
  preferredCandidateCount,
  onSetPreferredCandidateCount,
  onSetGlobalSearchAuthorized,
  onSetSearchPhase,
  onSetHasAttemptedCalibrationGeneration,
  onSetCalibrationComplete,
  onSetShowCalibrationModal,
  onGenerateCalibrationCandidates,
  onStartGlobalSearch,
  onJobCreated,
  onClose,
}: SearchCalibrationStageProps) {
  const { basicInfoFields } = useExpandedChatContext()

  return (
    <>
      {/* Phase 1: Search (no candidates yet) */}
      {searchPhase !== 'local-complete' && calibrationCandidates.length === 0 && (
        <div className="space-y-2.5">
          {/* Published Job Card */}
          <div className="p-3 bg-wedo-green/10 rounded-md border border-wedo-green/20">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-wedo-green/20 rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4 text-wedo-green" />
              </div>
              <div>
                <h4 className="text-xs font-medium text-lia-text-primary">
                  Vaga Publicada!
                </h4>
                <p className="text-micro text-lia-text-secondary">
                  {publishedJobId || 'JOB-XXXXX'} • {basicInfoFields.cargo}
                </p>
              </div>
            </div>
          </div>

          {/* Preferred Candidate Count Selector */}
          <div className="p-3 bg-lia-bg-primary/50 rounded-md border border-lia-border-subtle">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-lia-text-secondary" />
                <span className="text-sm text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                  Candidatos ideais:
                </span>
              </div>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((num) => (
                  <button
                    key={num}
                    onClick={() => onSetPreferredCandidateCount(num)}
                    className={`w-7 h-7 rounded-md text-sm font-medium transition-colors motion-reduce:transition-none ${
 preferredCandidateCount === num
                        ? 'bg-lia-btn-primary-bg text-lia-btn-primary-text'
                        : 'bg-lia-bg-tertiary text-lia-text-secondary hover:bg-lia-interactive-active'
                    }`}
                  >
                    {num}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Local Search Status */}
          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
            <div className="flex items-center gap-2 mb-2">
              <Database className="w-3.5 h-3.5 text-lia-text-secondary" />
              <span className="text-xs font-medium text-lia-text-primary">
                Busca na Base Interna
              </span>
            </div>

            {searchPhase === 'idle' || searchPhase === 'local-searching' ? (
              <div className="flex flex-col items-center justify-center py-4" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-6 h-6 text-lia-text-secondary animate-spin motion-reduce:animate-none mb-2" />
                <p className="text-xs text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                  Buscando candidatos na sua base de talentos...
                </p>
              </div>
            ) : (
              <div className="flex items-center justify-between p-2 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-wedo-green" />
                  <span className="text-xs text-lia-text-primary">
                    <span className="font-semibold text-wedo-green">{localCandidateCount}</span> candidatos encontrados
                  </span>
                </div>
                <span className="text-micro text-lia-text-secondary">Base interna</span>
              </div>
            )}
          </div>

          {/* Global Search Prompt */}
          {(searchPhase as string) === 'local-complete' && !globalSearchAuthorized && (
            <div className="p-3 bg-wedo-cyan/10 rounded-md border border-lia-border-default">
              <div className="flex items-start gap-2">
                <div className="w-8 h-8 bg-lia-bg-tertiary rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Globe className="w-4 h-4 text-lia-text-secondary" />
                </div>
                <div className="flex-1">
                  <h4 className="text-xs font-medium text-lia-text-primary mb-1">
                    Expandir para busca global?
                  </h4>
                  <p className="text-micro text-lia-text-secondary mb-2">
                    Posso buscar em uma base com mais de 800 milhões de perfis profissionais (Pearch AI).
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => {
                        onSetGlobalSearchAuthorized(true)
                        onStartGlobalSearch()
                      }}
                      className="px-3 py-1.5 bg-lia-btn-primary-bg text-lia-btn-primary-text text-micro font-medium rounded-md hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none flex items-center gap-1"
                    >
                      <Globe className="w-3 h-3" />
                      Sim, expandir busca
                    </button>
                    <button
                      onClick={() => onSetSearchPhase('global-complete')}
                      className="px-3 py-1.5 bg-lia-bg-secondary text-lia-text-secondary text-micro font-medium rounded-md hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none"
                    >
                      Não, usar só base local
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Global Search Loading */}
          {searchPhase === 'global-searching' && (
            <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
              <div className="flex items-center gap-2 mb-2">
                <Globe className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-primary">
                  Busca Global (Pearch AI)
                </span>
              </div>
              <div className="flex flex-col items-center justify-center py-4" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-6 h-6 text-lia-text-secondary animate-spin motion-reduce:animate-none mb-2" />
                <p className="text-xs text-lia-text-secondary">
                  Buscando em 800M+ perfis profissionais...
                </p>
              </div>
            </div>
          )}

          {/* Global Search Results */}
          {searchPhase === 'global-complete' && globalSearchAuthorized && globalCandidateCount > 0 && (
            <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
              <div className="flex items-center gap-2 mb-2">
                <Globe className="w-3.5 h-3.5 text-lia-text-secondary" />
                <span className="text-xs font-medium text-lia-text-primary">
                  Busca Global (Pearch AI)
                </span>
              </div>
              <div className="flex items-center justify-between p-2 bg-wedo-cyan/10 rounded-md">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-lia-text-secondary" />
                  <span className="text-xs text-lia-text-primary">
                    <span className="font-semibold text-lia-text-primary">+{globalCandidateCount}</span> candidatos encontrados
                  </span>
                </div>
                <span className="text-micro text-lia-text-secondary">Base global</span>
              </div>
            </div>
          )}

          {/* Search Analysis */}
          {searchPhase === 'global-complete' && (
            <div className="p-3 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-3.5 h-3.5 text-chat-cyan" />
                <span className="text-xs font-medium text-lia-text-primary">
                  Análise da Busca
                </span>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-micro">
                  <span className="lia-text-secondary" aria-live="polite" aria-atomic="true">Total de candidatos:</span>
                  <span className="font-semibold text-lia-text-primary">{localCandidateCount + (globalSearchAuthorized ? globalCandidateCount : 0)}</span>
                </div>
                <div className="flex items-center justify-between text-micro">
                  <span className="lia-text-secondary">Base interna:</span>
                  <span className="font-medium text-wedo-green">{localCandidateCount}</span>
                </div>
                {globalSearchAuthorized && globalCandidateCount > 0 && (
                  <div className="flex items-center justify-between text-micro">
                    <span className="lia-text-secondary">Base global:</span>
                    <span className="font-medium text-lia-text-secondary">{globalCandidateCount}</span>
                  </div>
                )}
                <div className="pt-2 border-t border-lia-border-subtle">
                  <p className="text-micro text-lia-text-secondary italic" aria-live="polite" aria-atomic="true">
                    {localCandidateCount >= 10
                      ? 'Ótima quantidade! Você tem candidatos suficientes para uma boa seleção.'
                      : localCandidateCount >= 5
                        ? 'Quantidade razoável. Considere expandir a busca se precisar de mais opções.'
                        : 'Poucos candidatos encontrados. Recomendo expandir para busca global.'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Advance to Calibration Button */}
          {searchPhase === 'global-complete' && (
            <div className="p-3 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-8 h-8 bg-wedo-green/10 rounded-full flex items-center justify-center">
                  <Target className="w-4 h-4 text-wedo-green" />
                </div>
                <div className="flex-1">
                  <h4 className="text-xs font-medium text-lia-text-primary">
                    Próximo passo: Calibração
                  </h4>
                  <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                    Vou apresentar 3 candidatos para você avaliar e calibrar minha assertividade
                  </p>
                </div>
              </div>
              <button
                onClick={() => onSetShowCalibrationModal(true)}
                className="w-full py-2 bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs font-medium rounded-md hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
              >
                <Users className="w-4 h-4" />
                Iniciar Calibração de Candidatos
              </button>
            </div>
          )}
        </div>
      )}

      {/* Phase 2: Calibration (candidates available, not complete) */}
      {calibrationCandidates.length > 0 && !calibrationComplete && (
        <div className="space-y-2.5" role="status" aria-live="polite" aria-label="Carregando...">
          {/* Loading state */}
          {isLoadingCalibration && (
            <div className="p-4 bg-lia-bg-secondary rounded-md border border-lia-border-subtle" role="status" aria-live="polite" aria-label="Carregando...">
              <div className="flex items-center gap-3" role="status" aria-live="polite" aria-label="Carregando...">
                <Loader2 className="w-5 h-5 text-lia-text-secondary animate-spin motion-reduce:animate-none" />
                <div>
                  <h4 className="text-xs font-medium text-lia-text-primary">
                    Buscando candidatos...
                  </h4>
                  <p className="text-micro text-lia-text-secondary">
                    Aguarde enquanto encontro perfis compatíveis
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* No candidates found - fallback UI */}
          {!isLoadingCalibration && calibrationCandidates.length === 0 && hasAttemptedCalibrationGeneration && (
            <div className="p-4 bg-lia-bg-secondary rounded-md border border-status-warning/30">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-status-warning/20 rounded-full flex items-center justify-center flex-shrink-0">
                  <AlertTriangle className="w-4 h-4 text-status-warning" />
                </div>
                <div className="flex-1">
                  <h4 className="text-xs font-medium text-lia-text-primary">
                    Nenhum candidato encontrado
                  </h4>
                  <p className="text-micro text-lia-text-secondary mt-1" aria-live="polite" aria-atomic="true">
                    Não encontrei candidatos na base que correspondam aos critérios. Você pode tentar novamente ou prosseguir diretamente para a busca ativa.
                  </p>
                  <div className="flex gap-2 mt-3">
                    <button
                      onClick={() => {
                        onSetHasAttemptedCalibrationGeneration(false)
                        onGenerateCalibrationCandidates()
                      }}
                      className="flex-1 py-2 bg-lia-bg-primary text-lia-text-primary text-xs font-medium rounded-md border border-lia-border-default hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none flex items-center justify-center gap-1.5"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      Tentar Novamente
                    </button>
                    <button
                      onClick={() => onSetCalibrationComplete(true)}
                      className="flex-1 py-2 bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs font-medium rounded-md hover:bg-lia-btn-primary-hover transition-colors motion-reduce:transition-none flex items-center justify-center gap-1.5"
                    >
                      <ChevronRight className="w-3.5 h-3.5" />
                      Prosseguir Mesmo Assim
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Calibration Info Card - only show when candidates exist */}
          {!isLoadingCalibration && calibrationCandidates.length > 0 && (
            <>
              <div className="p-3 bg-lia-bg-secondary rounded-md border border-lia-border-subtle">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 bg-lia-bg-tertiary rounded-full flex items-center justify-center">
                    <Target className="w-4 h-4 text-lia-text-secondary" />
                  </div>
                  <div>
                    <h4 className="text-xs font-medium text-lia-text-primary">
                      Calibração em andamento
                    </h4>
                    <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                      Avalie os candidatos para calibrar a assertividade da LIA
                    </p>
                  </div>
                </div>
              </div>

              {/* Calibration Progress */}
              <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-medium text-lia-text-primary">Progresso</span>
                  <span className="text-xs text-lia-text-secondary font-semibold">{approvedCandidates.length}/3 aprovados</span>
                </div>
                <div className="w-full bg-lia-interactive-active rounded-full h-2">
                  <div
                    className="bg-lia-btn-primary-bg h-2 rounded-full transition-[width,height] duration-300"
                    style={{width: `${(approvedCandidates.length / 3) * 100}%`}}
                  />
                </div>
              </div>

              {/* Open Modal Button */}
              {!showCalibrationModal && (
                <button
                  onClick={() => onSetShowCalibrationModal(true)}
                  className="w-full py-2 bg-lia-btn-primary-bg text-lia-btn-primary-text text-xs font-medium rounded-md hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
                >
                  <Users className="w-4 h-4" />
                  Abrir Modal de Candidatos
                </button>
              )}
            </>
          )}
        </div>
      )}

      {/* Phase 3: Post-calibration success */}
      {calibrationComplete && (
        <div className="space-y-2.5">
          {/* Success Header */}
          <div className="p-3 bg-wedo-green/10 rounded-md border border-wedo-green/20">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-wedo-green flex items-center justify-center">
                <CheckCircle2 className="w-4 h-4 text-white" />
              </div>
              <div>
                <h3 className="text-xs font-semibold text-lia-text-primary">
                  Perfeito! Vaga Configurada com Sucesso
                </h3>
                <p className="text-micro text-lia-text-secondary" aria-live="polite" aria-atomic="true">
                  A partir de agora os candidatos serão automaticamente adicionados na vaga.
                </p>
              </div>
            </div>
          </div>

          {/* O que acontece agora */}
          <div className="p-3 bg-lia-bg-primary border border-lia-border-subtle rounded-md">
            <h4 className="text-xs font-semibold text-lia-text-primary mb-3">
              O que acontece agora:
            </h4>
            <ul className="space-y-2.5">
              {[
                { icon: <FileText className="w-3 h-3 text-lia-text-secondary" />, bg: 'bg-lia-bg-tertiary', text: <><strong>O plano de trabalho</strong> será enviado por e-mail para todos os envolvidos na vaga</> },
                { icon: <BarChart3 className="w-3 h-3 text-wedo-purple" />, bg: 'bg-wedo-purple/10', text: <><strong>Relatórios de progresso</strong> serão enviados automaticamente a cada 5 dias por e-mail</> },
                { icon: <Users className="w-3 h-3 text-wedo-green" />, bg: 'bg-wedo-green/10', text: <><strong>Candidatos inscritos</strong> via website serão automaticamente triados por mim e você será notificado via <strong>Teams</strong></> },
                { icon: <Calendar className="w-3 h-3 text-wedo-magenta" />, bg: 'bg-wedo-magenta/10', text: <>Vou cuidar da sua <strong>agenda</strong>, avisando sobre tarefas pendentes como sua assistente de recrutamento inteligente</> },
                { icon: <Bell className="w-3 h-3 text-status-warning" />, bg: 'bg-status-warning/10', text: <><strong>Lembretes de feedback</strong> serão enviados quando candidatos estiverem aguardando resposta há muito tempo</> },
                { icon: <Clock className="w-3 h-3 text-lia-text-secondary" />, bg: 'bg-lia-bg-tertiary', text: <><strong>SLAs de resposta</strong> serão monitorados para cada etapa do processo seletivo</> },
                { icon: <MessageSquare className="w-3 h-3 text-wedo-cyan" />, bg: 'bg-wedo-cyan/10', text: <><strong>Comunicação automática</strong> com candidatos sobre o status do processo será gerenciada por mim</> },
                { icon: <Rocket className="w-3 h-3 text-lia-text-secondary" />, bg: 'bg-lia-bg-tertiary', text: <>Quando houver candidatos aprovados, seguirei com a <strong>triagem</strong> e posteriormente com os <strong>agendamentos de entrevistas</strong>!</> },
              ].map((item, idx) => (
                <li key={idx} className="flex items-start gap-2">
                  <div className={cn('w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5', item.bg)}>
                    {item.icon}
                  </div>
                  <p className="text-xs text-lia-text-primary leading-relaxed">{item.text}</p>
                </li>
              ))}
            </ul>
          </div>

          {/* Nota final */}
          <div className="p-2.5 bg-lia-bg-secondary rounded-md">
            <p className="text-micro text-lia-text-secondary text-center italic" aria-live="polite" aria-atomic="true">
              *Todos estes detalhes serão enviados por e-mail junto com a confirmação de abertura da vaga.
            </p>
          </div>

          {/* Botão para ir para tabela */}
          <button
            onClick={() => {
              onJobCreated?.()
              onClose()
            }}
            className="w-full py-2.5 bg-lia-btn-primary-bg text-lia-btn-primary-text rounded-md text-xs font-semibold hover:bg-lia-btn-primary-hover dark:hover:bg-lia-interactive-active transition-colors motion-reduce:transition-none flex items-center justify-center gap-2"
          >
            <ExternalLink className="w-4 h-4" />
            Ver Candidatos no Kanban
          </button>
        </div>
      )}
    </>
  )
}

/**
 * SearchCalibrationNavButtons — botões de navegação para a etapa search-calibration.
 * Separado para uso no footer do sidebar.
 */
interface SearchCalibrationNavButtonsProps {
  calibrationCandidates: CalibrationCandidate[]
  calibrationComplete: boolean
  isLoadingCalibration: boolean
  hasAttemptedCalibrationGeneration: boolean
  approvedCandidates: string[]
  onSetShowCalibrationModal: (val: boolean) => void
}

export function SearchCalibrationNavButtons({
  calibrationCandidates,
  calibrationComplete,
  isLoadingCalibration,
  hasAttemptedCalibrationGeneration,
  approvedCandidates,
  onSetShowCalibrationModal,
}: SearchCalibrationNavButtonsProps) {
  if (calibrationComplete) {
    return (
      <div className="text-center text-micro text-wedo-green font-medium">
        Calibração concluída! Candidatos sendo adicionados ao kanban...
      </div>
    )
  }

  return (
    <div className="flex gap-3">
      {calibrationCandidates.length === 0 && hasAttemptedCalibrationGeneration && !isLoadingCalibration ? (
        <div className="w-full text-center text-micro text-lia-text-secondary">
          Use os botões acima para tentar novamente ou prosseguir
        </div>
      ) : (
        <Button
          className="w-full h-9 rounded-md text-xs font-medium bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
         
          onClick={() => {
            if (calibrationCandidates.length > 0) {
              onSetShowCalibrationModal(true)
            }
          }}
          disabled={calibrationCandidates.length === 0 || isLoadingCalibration}
        >
          {isLoadingCalibration ? (
            <>
              <Loader2 className="w-3.5 h-3.5 mr-1.5 animate-spin motion-reduce:animate-none" />
              Carregando...
            </>
          ) : (
            <>
              <Eye className="w-3.5 h-3.5 mr-1.5" />
              Continuar Calibração ({approvedCandidates.length}/3)
            </>
          )}
        </Button>
      )}
    </div>
  )
}
