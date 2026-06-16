"use client"

import React from"react"
import { Button } from"@/components/ui/button"
import { Chip } from "@/components/ui/chip"
import { Avatar, AvatarFallback, AvatarImage } from"@/components/ui/avatar"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from"@/components/ui/select"
import {
  ArrowRight, X, Brain, CheckCircle, BrainCircuit, FileText, Languages
} from"lucide-react"
import { formatScorePercent } from"@/lib/design-tokens"
import { calculateNotaLiaGeral } from"@/components/pages/job-kanban/utils/kanbanHelpers"
import { useTranslations } from "next-intl"
import type { KanbanPageCoreState } from"./hooks/useKanbanPageCore"

export function KanbanPageModalsInline(state: KanbanPageCoreState) {
  const t = useTranslations('kanban')
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
            className="relative bg-lia-bg-primary rounded-xl w-full max-w-md mx-4 overflow-hidden border border-lia-border-subtle"
           
          >
            <div className="flex items-center justify-between px-6 py-4 bg-lia-bg-secondary">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-lia-bg-tertiary flex items-center justify-center">
                  <ArrowRight className="w-5 h-5 text-lia-text-secondary" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-lia-text-primary">
                    {t('confirmMovement')}
                  </h2>
                  <p className="text-sm text-lia-text-secondary">
                    {t('selectDetailedStatus')}
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
              <div className="flex items-center gap-3 p-3 bg-lia-bg-secondary rounded-xl">
                <Avatar className="w-10 h-10">
                  <AvatarImage src={pendingMove.candidate.avatar as string | undefined} alt={pendingMove.candidate.name as string} />
                  <AvatarFallback>{(pendingMove.candidate.name as string | undefined)?.split(' ').map((n: string) => n[0]).join('') || 'C'}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium text-lia-text-primary">{pendingMove.candidate.name as string}</p>
                  <p className="text-sm text-lia-text-secondary">{((pendingMove.candidate.role as string | undefined) || (pendingMove.candidate.cargo as string | undefined) || t('candidateFallback'))}</p>
                </div>
              </div>

              <div className="flex items-center gap-3 justify-center">
                <div className="px-3 py-2 bg-lia-bg-tertiary rounded-xl">
                  <span className="text-sm font-medium text-lia-text-secondary">
                    {getStageDisplayName(pendingMove.fromColumn)}
                  </span>
                </div>
                <ArrowRight className="w-5 h-5 text-lia-text-muted" />
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
                    {t('suggestedStatusByLIA')}
                  </label>
                  <div 
                    className={`p-3 rounded-md border-2 cursor-pointer transition-colors motion-reduce:transition-none ${
                      selectedSubStatus === getSuggestedSubStatus(pendingMove.toColumn)
                        ? 'bg-lia-bg-tertiary border-lia-border-medium'
                        : 'bg-lia-bg-secondary border-lia-border-subtle hover:border-lia-border-default'
                    }`}
                    onClick={() => setSelectedSubStatus(getSuggestedSubStatus(pendingMove.toColumn))}
                  >
                    <Chip density="relaxed" variant="neutral" muted>
                      {getAvailableSubStatuses(pendingMove.toColumn).find(s => s.name === getSuggestedSubStatus(pendingMove.toColumn))?.displayName || getSuggestedSubStatus(pendingMove.toColumn)}
                    </Chip>
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-lia-text-secondary">
                  {t('selectOtherStatus')}
                </label>
                <Select 
                  value={selectedSubStatus} 
                  onValueChange={setSelectedSubStatus}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder={t('selectAStatus')} />
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
                {t('cancelAction')}
              </Button>
              <Button
                onClick={confirmMove}
                disabled={!selectedSubStatus}
                className="px-4 text-lia-btn-primary-text bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover"
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                {t('approve').replace(/ar$/, 'ar') === t('approve') ? t('confirmMovement').split(' ')[0] : t('approve')}
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
            className="relative bg-lia-bg-primary rounded-xl w-full max-w-2xl mx-4 max-h-[85vh] overflow-hidden border border-lia-border-subtle"
           
          >
            <div className="flex items-center justify-between px-6 py-4 bg-lia-bg-secondary">
              <div className="flex items-center gap-3">
                {activeModal === 'scoreGeral' && <BrainCircuit className="w-5 h-5 text-lia-text-primary" />}
                {activeModal === 'triagem' && <BrainCircuit className="w-5 h-5 text-wedo-cyan-text" />}
                {activeModal === 'testeTecnico' && <FileText className="w-5 h-5 text-lia-text-secondary" />}
                {activeModal === 'testeIngles' && <Languages className="w-5 h-5 text-lia-text-secondary" />}
                <div>
                  <h2 className="text-lg font-semibold text-lia-text-primary">
                    {activeModal === 'scoreGeral' && t('overallScoreTitle')}
                    {activeModal === 'triagem' && t('screeningScoreTitle')}
                    {activeModal === 'testeTecnico' && t('technicalTestTitle')}
                    {activeModal === 'testeIngles' && t('englishTestTitle')}
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
              {activeModal === 'scoreGeral' && (
                <div className="space-y-6">
                  <div className="text-center py-8">
                    <div className="inline-flex items-center justify-center w-24 h-24 rounded-full bg-lia-bg-tertiary mb-4">
                      <span className="text-4xl font-semibold text-lia-text-primary">
                        {calculateNotaLiaGeral(selectedCandidateForModal as unknown as Parameters<typeof calculateNotaLiaGeral>[0])}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">{t('overallCandidateScore')}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-lia-bg-secondary rounded-xl">
                      <p className="text-xs text-lia-text-tertiary mb-1">{t('screeningScoreLabel')}</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {formatScorePercent((selectedCandidateForModal.liaScore ?? selectedCandidateForModal.score) as number | null | undefined, 0)}
                      </p>
                    </div>
                    <div className="p-4 bg-lia-bg-secondary rounded-xl">
                      <p className="text-xs text-lia-text-tertiary mb-1">{t('cvScoreLabel')}</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {formatScorePercent((selectedCandidateForModal.skillsMatch as number | undefined) || (selectedCandidateForModal.fitScore as number | undefined) || 0, 0)}
                      </p>
                    </div>
                    <div className="p-4 bg-lia-bg-secondary rounded-xl">
                      <p className="text-xs text-lia-text-tertiary mb-1">{t('technicalTestScoreLabel')}</p>
                      <p className="text-lg font-semibold text-lia-text-primary">
                        {(selectedCandidateForModal.technicalTestScore as number | null | undefined) !== null && selectedCandidateForModal.technicalTestScore !== undefined
                          ? formatScorePercent(selectedCandidateForModal.technicalTestScore as number, 0)
                          : '—'}
                      </p>
                    </div>
                    <div className="p-4 bg-lia-bg-secondary rounded-xl">
                      <p className="text-xs text-lia-text-tertiary mb-1">{t('englishTestScoreLabel')}</p>
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
                      <span className="text-3xl font-semibold text-lia-text-primary">
                        {formatScorePercent((selectedCandidateForModal.liaScore ?? selectedCandidateForModal.score) as number | null | undefined, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">{t('liaScreeningScore')}</p>
                  </div>
                  <div className="p-4 bg-lia-bg-secondary rounded-xl">
                    <h4 className="text-sm font-semibold text-lia-text-primary mb-3">{t('liaAnalysisTitle')}</h4>
                    <p className="text-sm text-lia-text-secondary leading-relaxed">
                      {t('liaAnalysisText')}
                    </p>
                  </div>
                </div>
              )}

              {activeModal === 'testeTecnico' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 ${(selectedCandidateForModal.technicalTestScore as number) >= 80 ? 'bg-status-success' : (selectedCandidateForModal.technicalTestScore as number) >= 60 ? 'bg-status-warning' : 'bg-lia-border-medium'}`}
                    >
                      <span className="text-3xl font-semibold text-lia-text-primary">
                        {formatScorePercent(selectedCandidateForModal.technicalTestScore as number | null | undefined, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">{t('technicalTestResult')}</p>
                  </div>
                  <div className="p-4 bg-lia-bg-secondary rounded-xl">
                    <h4 className="text-sm font-semibold text-lia-text-primary mb-3">{t('testDetailsTitle')}</h4>
                    <p className="text-sm text-lia-text-secondary leading-relaxed">
                      {t('testDetailsText')}
                    </p>
                  </div>
                </div>
              )}

              {activeModal === 'testeIngles' && (
                <div className="space-y-6">
                  <div className="text-center py-6">
                    <div 
                      className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-4 ${(selectedCandidateForModal.englishTestScore as number) >= 80 ? 'bg-status-success' : (selectedCandidateForModal.englishTestScore as number) >= 60 ? 'bg-lia-border-default' : 'bg-lia-border-medium'}`}
                    >
                      <span className="text-3xl font-semibold text-lia-text-primary">
                        {formatScorePercent(selectedCandidateForModal.englishTestScore as number | null | undefined, 0)}
                      </span>
                    </div>
                    <p className="text-sm text-lia-text-secondary">{t('englishTestResult')}</p>
                  </div>
                  <div className="p-4 bg-lia-bg-secondary rounded-xl">
                    <h4 className="text-sm font-semibold text-lia-text-primary mb-3">{t('proficiencyLevelTitle')}</h4>
                    <p className="text-sm text-lia-text-secondary leading-relaxed">
                      {t('proficiencyText')}
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
                className="px-4 py-2 text-sm font-medium text-lia-text-primary bg-lia-bg-secondary border border-lia-border-default rounded-xl hover:bg-lia-interactive-hover transition-colors motion-reduce:transition-none"
              >
                {t('closePanel')}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
