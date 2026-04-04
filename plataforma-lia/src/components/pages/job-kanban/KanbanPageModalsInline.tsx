"use client"

import React from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ArrowRight, X, Brain, CheckCircle, BrainCircuit, FileText, Languages
} from "lucide-react"
import { formatScorePercent } from "@/lib/design-tokens"
import { calculateNotaLiaGeral } from "@/components/pages/job-kanban/utils/kanbanHelpers"
import type { KanbanPageCoreState } from "./hooks/useKanbanPageCore"

export function KanbanPageModalsInline(state: KanbanPageCoreState) {
  const {
    statusModalOpen, pendingMove, cancelMove, getStageDisplayName,
    getSuggestedSubStatus, selectedSubStatus, setSelectedSubStatus, getAvailableSubStatuses, getSubStatusColor, confirmMove,
    activeModal, setActiveModal, selectedCandidateForModal, setSelectedCandidateForModal,
  } = state
  return (
    <>
      {statusModalOpen && pendingMove && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-lia-overlay backdrop-blur-sm"
            onClick={cancelMove}
          />
          <div 
            className="relative bg-lia-bg-primary rounded-md w-full max-w-md mx-4 overflow-hidden border border-lia-border-subtle"
           
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle bg-lia-bg-secondary">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary flex items-center justify-center">
                  <ArrowRight className="w-5 h-5 text-lia-text-secondary" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-lia-text-primary">
                    Confirmar Movimentação
                  </h2>
                  <p className="text-sm text-lia-text-secondary">
                    Selecione o status detalhado
                  </p>
                </div>
              </div>
              <button
                onClick={cancelMove}
                className="p-2 hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none"
              >
                <X className="w-5 h-5 text-lia-text-tertiary" />
              </button>
            </div>

            <div className="p-6 space-y-5">
              <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary rounded-md">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={pendingMove.candidate.avatar as string | undefined} alt={pendingMove.candidate.name as string} />
                  <AvatarFallback>{(pendingMove.candidate.name as string | undefined)?.split(' ').map((n: string) => n[0]).join('') || 'C'}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-lia-text-primary">{pendingMove.candidate.name as string}</p>
                  <p className="text-sm text-lia-text-secondary">{((pendingMove.candidate.role as string | undefined) || (pendingMove.candidate.cargo as string | undefined) || 'Candidato')}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 justify-center">
                <div className="px-3 py-2 bg-lia-bg-tertiary rounded-md">
                  <span className="text-sm font-medium text-lia-text-secondary">
                    {getStageDisplayName(pendingMove.fromColumn)}
                  </span>
                </div>
                <ArrowRight className="w-5 h-5 text-lia-text-disabled" />
                <div className="px-3 py-2 bg-lia-btn-primary-bg rounded-md">
                  <span className="text-sm font-medium text-lia-btn-primary-text">
                    {getStageDisplayName(pendingMove.toColumn)}
                  </span>
                </div>
              </div>

              {getSuggestedSubStatus(pendingMove.toColumn) && (
                <div className="space-y-2">
                  <label className="text-sm font-medium text-lia-text-secondary flex items-center gap-2">
                    <Brain className="w-4 h-4 text-wedo-cyan" />
                    Status Sugerido pela LIA
                  </label>
                  <div 
                    className={`p-3 rounded-md border-2 cursor-pointer transition-colors motion-reduce:transition-none ${
                      selectedSubStatus === getSuggestedSubStatus(pendingMove.toColumn)
                        ? 'bg-lia-bg-tertiary border-lia-border-medium'
                        : 'bg-lia-bg-secondary border-lia-border-subtle hover:border-lia-border-default'
                    }`}
                    onClick={() => setSelectedSubStatus(getSuggestedSubStatus(pendingMove.toColumn))}
                  >
                    <Badge 
                      className="text-sm px-3 py-1 font-medium border-0 text-lia-text-primary bg-lia-btn-primary-bg"
                    >
                      {getAvailableSubStatuses(pendingMove.toColumn).find(s => s.name === getSuggestedSubStatus(pendingMove.toColumn))?.displayName || getSuggestedSubStatus(pendingMove.toColumn)}
                    </Badge>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-lia-text-secondary">
                  Selecionar outro status
                </label>
                <Select 
                  value={selectedSubStatus} 
                  onValueChange={setSelectedSubStatus}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Selecione um status" />
                  </SelectTrigger>
                  <SelectContent className="max-h-60">
                    {getAvailableSubStatuses(pendingMove.toColumn).map((status) => {
                      const colors = getSubStatusColor(status)
                      return (
                        <SelectItem 
                          key={status.name} 
                          value={status.name}
                          className="cursor-pointer"
                        >
                          <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-sm font-medium ${colors.bg} ${colors.text}`}>
                            {status.displayName}
                          </span>
                        </SelectItem>
                      )
                    })}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-lia-border-subtle bg-lia-bg-secondary">
              <Button
                variant="outline"
                onClick={cancelMove}
                className="px-4"
              >
                Cancelar
              </Button>
              <Button
                onClick={confirmMove}
                disabled={!selectedSubStatus}
                className="px-4 text-lia-btn-primary-text bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                Confirmar
              </Button>
            </div>
          </div>
        </div>
      )}

      {activeModal && selectedCandidateForModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div 
            className="absolute inset-0 bg-lia-overlay backdrop-blur-sm"
            onClick={() => {
              setActiveModal(null)
              setSelectedCandidateForModal(null)
            }}
          />
          <div 
            className="relative bg-lia-bg-primary rounded-md w-full max-w-2xl mx-4 max-h-[85vh] overflow-hidden border border-lia-border-subtle"
           
          >
            <div className="flex items-center justify-between px-6 py-4 border-b border-lia-border-subtle bg-lia-bg-secondary">
              <div className="flex items-center gap-3">
                {activeModal === 'notaGeral' && <BrainCircuit className="w-5 h-5 text-lia-text-primary" />}
                {activeModal === 'triagem' && <BrainCircuit className="w-5 h-5 text-wedo-cyan" />}
                {activeModal === 'testeTecnico' && <FileText className="w-5 h-5 text-lia-text-secondary" />}
                {activeModal === 'testeIngles' && <Languages className="w-5 h-5 text-lia-text-secondary" />}
                <div>
                  <h2 className="text-lg font-semibold text-lia-text-primary">
                    {activeModal === 'notaGeral' && 'Nota Geral'}
                    {activeModal === 'triagem' && 'Nota Triagem'}
                    {activeModal === 'testeTecnico' && 'Teste Técnico'}
                    {activeModal === 'testeIngles' && 'Teste Inglês'}
                  </h2>
                  <p className="text-sm text-lia-text-secondary">{selectedCandidateForModal.name as string}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setActiveModal(null)
                  setSelectedCandidateForModal(null)
                }}
                className="p-2 hover:bg-lia-interactive-hover rounded-md transition-colors motion-reduce:transition-none"
              >
                <X className="w-5 h-5 text-lia-text-tertiary" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto max-h-[calc(85vh-140px)]">
              {activeModal === 'notaGeral' && (
                <div className="space-y-6">
                  <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-lia-bg-tertiary mb-4">
                      <span className="text-4xl font-bold text-lia-text-primary">
                        {calculateNotaLiaGeral(selectedCandidateForModal as unknown as Parameters<typeof calculateNotaLiaGeral>[0])}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">Pontuação Geral do Candidato</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-lia-bg-secondary rounded-md">
                      <p className="text-xs text-lia-text-tertiary mb-1">Nota Triagem</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {formatScorePercent((selectedCandidateForModal.liaScore ?? selectedCandidateForModal.score) as number | null | undefined, 0)}
                      </p>
                    </div>
                    <div className="p-4 bg-lia-bg-secondary rounded-md">
                      <p className="text-xs text-lia-text-tertiary mb-1">Nota CV</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {formatScorePercent((selectedCandidateForModal.skillsMatch as number | undefined) || (selectedCandidateForModal.fitScore as number | undefined) || 0, 0)}
                      </p>
                    </div>
                    <div className="p-4 bg-lia-bg-secondary rounded-md">
                      <p className="text-xs text-lia-text-tertiary mb-1">Teste Técnico</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {(selectedCandidateForModal.technicalTestScore as number | null | undefined) !== null && selectedCandidateForModal.technicalTestScore !== undefined
                          ? formatScorePercent(selectedCandidateForModal.technicalTestScore as number, 0)
                          : '—'}
                      </p>
                    </div>
                    <div className="p-4 bg-lia-bg-secondary rounded-md">
                      <p className="text-xs text-lia-text-tertiary mb-1">Teste Inglês</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {(selectedCandidateForModal.englishTestScore as number | null | undefined) !== null && selectedCandidateForModal.englishTestScore !== undefined
                          ? formatScorePercent(selectedCandidateForModal.englishTestScore as number, 0)
                          : '—'}
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {activeModal === 'triagem' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 bg-lia-bg-tertiary"
                    >
                      <span className="text-3xl font-bold text-lia-text-primary">
                        {formatScorePercent((selectedCandidateForModal.liaScore ?? selectedCandidateForModal.score) as number | null | undefined, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">Score de Triagem LIA</p>
                  </div>
                  <div className="p-4 bg-lia-bg-secondary rounded-md">
                    <h4 className="text-sm font-semibold text-lia-text-primary mb-3">Análise da LIA</h4>
                    <p className="text-sm text-lia-text-secondary leading-relaxed">
                      Candidato avaliado automaticamente pela LIA com base em critérios de experiência, 
                      competências e aderência ao perfil da vaga. A triagem considera fatores como 
                      histórico profissional, formação acadêmica e habilidades técnicas declaradas.
                    </p>
                  </div>
                </div>
              )}

              {activeModal === 'testeTecnico' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4"
                      style={{backgroundColor: (selectedCandidateForModal.technicalTestScore as number) >= 80 ? 'var(--status-success)' :
                                         (selectedCandidateForModal.technicalTestScore as number) >= 60 ? 'var(--status-warning)' :
                                         (selectedCandidateForModal.technicalTestScore as number) >= 40 ? 'var(--lia-border-medium)' :
                                         'var(--lia-border-medium)'}}
                    >
                      <span className="text-3xl font-bold text-lia-text-primary">
                        {formatScorePercent(selectedCandidateForModal.technicalTestScore as number | null | undefined, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">Resultado do Teste Técnico</p>
                  </div>
                  <div className="p-4 bg-lia-bg-secondary rounded-md">
                    <h4 className="text-sm font-semibold text-lia-text-primary mb-3">Detalhes do Teste</h4>
                    <p className="text-sm text-lia-text-secondary leading-relaxed">
                      Avaliação técnica realizada através de teste prático com foco nas competências 
                      técnicas requeridas para a posição. Inclui análise de código, resolução de 
                      problemas e conhecimento de ferramentas específicas.
                    </p>
                  </div>
                </div>
              )}

              {activeModal === 'testeIngles' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className="inline-flex items-center justify-center w-20 h-20 rounded-full mb-4"
                      style={{backgroundColor: (selectedCandidateForModal.englishTestScore as number) >= 80 ? 'var(--status-success)' :
                                         (selectedCandidateForModal.englishTestScore as number) >= 60 ? 'var(--lia-border-default)' :
                                         (selectedCandidateForModal.englishTestScore as number) >= 40 ? 'var(--lia-border-medium)' :
                                         'var(--lia-border-medium)'}}
                    >
                      <span className="text-3xl font-bold text-lia-text-primary">
                        {formatScorePercent(selectedCandidateForModal.englishTestScore as number | null | undefined, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">Resultado do Teste de Inglês</p>
                  </div>
                  <div className="p-4 bg-lia-bg-secondary rounded-md">
                    <h4 className="text-sm font-semibold text-lia-text-primary mb-3">Nível de Proficiência</h4>
                    <p className="text-sm text-lia-text-secondary leading-relaxed">
                      Avaliação de proficiência em inglês cobrindo compreensão escrita, 
                      expressão oral e vocabulário técnico relevante para a posição.
                    </p>
                  </div>
                </div>
              )}

            </div>

            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-lia-border-subtle bg-lia-bg-secondary">
              <button
                onClick={() => {
                  setActiveModal(null)
                  setSelectedCandidateForModal(null)
                }}
                className="px-4 py-2 text-sm font-medium text-lia-text-primary bg-lia-bg-secondary border border-lia-border-default rounded-md hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
              >
                Fechar
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
