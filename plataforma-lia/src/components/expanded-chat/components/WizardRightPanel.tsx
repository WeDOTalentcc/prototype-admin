"use client"

/**
 * WizardRightPanel — painel lateral direito do wizard de criação de vaga.
 * Extraído de expanded-chat-modal.tsx (Sprint 4.6 — 2026-03-28).
 * Portabilidade Vue: props → defineProps; callbacks → emit (on*).
 */

import React from "react"
import { Brain, ChevronLeft, Check, Rocket } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import type { WizardStage, ExtendedWizardStageConfig } from "../config"
import type { WSIQualityField } from "../hooks/useWSIQualityGates"
import type { CatalogStatus } from "./WizardHeader"
import { WizardHeader } from "./WizardHeader"
import { WSIQualityBar } from "./WSIQualityBar"
import {
  SalaryStage,
  CompetenciesStage,
  WSIQuestionsStage,
  EnrichedJDStage,
  SearchCalibrationStage,
  SearchCalibrationNavButtons,
  ReviewPublishStage,
  InputEvaluationStage,
  type EnrichedJDData,
} from "../stages"
import type { SalaryBenchmark } from "../stages/SalaryStage"
import type { WSIQuestionCandidate, CompanyDefaultQuestion } from "../stages/WSIQuestionsStage"
import type { ReviewPublishStageProps } from "../stages/ReviewPublishStage"
import type { FastTrackSuggestion } from "@/hooks/useFastTrack"
import type {
  BasicInfoFields,
  DetectedCriteria,
  TechnicalSkill,
  BehavioralCompetency,
  SalaryInfo,
} from "../ExpandedChatContext"
import type { CalibrationCandidate } from "../types"
import type { PublishingPlatform, JobConfig } from "../hooks/usePublishingState"
import type { SkillWeightInference } from "../stages/CompetenciesStage"

// ─── Types re-exported from stage types ──────────────────────────────────────

type CriteriaItem = {
  key: string
  label: string
  value: string | string[] | null
}

type SearchPhase = 'idle' | 'local-searching' | 'local-complete' | 'global-searching' | 'global-complete'

type CompanyConfig = {
  workModel?: string
  hybridDaysOnsite?: number
  employmentTypes?: string[]
  techStack?: string[]
  values?: string[]
  coreCompetencies?: string[]
  departments?: { id: string; name: string }[]
  benefits?: { name: string; category: string; value?: number; is_active: boolean }[]
  evpBullets?: string[]
  headquarters?: string
  locations?: string[]
} | null

// ─── Props Interface ──────────────────────────────────────────────────────────

export interface WizardRightPanelProps {
  // Layout
  panelWidth: number
  resizeRef: React.RefObject<HTMLDivElement | null>

  // Stage navigation
  currentStage: WizardStage
  currentStageIndex: number
  currentStageConfig: ExtendedWizardStageConfig | undefined

  // Panel state
  stageTransition: 'idle' | 'loading' | 'waiting-response'
  isFullscreen: boolean
  catalogStatus?: CatalogStatus | null

  // Auto-save
  isAutoSaving: boolean
  autoSaveLastSaved: Date | null
  hasPendingChanges: boolean
  hasRestoredDraft: boolean
  getLastSavedText: () => string | null

  // WSI quality gates
  wsiQualityGates: {
    score: number
    fields: WSIQualityField[]
    summaryText: string
    scoreColor: 'green' | 'yellow' | 'red'
    canAdvance: boolean
  }

  // InputEvaluationStage props
  configLoaded: boolean
  hasConfigData: boolean
  criteriaItems: CriteriaItem[]
  isHighlighted: (key: string) => boolean
  hasFastTrackSuggestions: boolean
  fastTrackIsLoading: boolean
  fastTrackSuggestions: FastTrackSuggestion[]
  fastTrackSelectedJob: FastTrackSuggestion | null
  fastTrackSuggestionsShownTracked: boolean
  onFastTrackSelectJob: (job: FastTrackSuggestion) => void
  onFastTrackDismiss: () => void

  // EnrichedJDStage props
  enrichedJDData: EnrichedJDData | null
  isLoadingEnrichment: boolean
  detectedCriteria: DetectedCriteria
  onAcceptEnrichedSuggestion: (suggestionId: string) => void
  onRejectEnrichedSuggestion: (suggestionId: string) => void
  onAcceptAllEnrichedSuggestions: () => void

  // CompetenciesStage props
  technicalSkills: TechnicalSkill[]
  behavioralCompetencies: BehavioralCompetency[]
  highlightedFields: Set<string>
  basicInfoFields: BasicInfoFields
  companyConfig: CompanyConfig
  inferSkillWeight: (skill: string, cargo: string, senioridade: string, area: string, type: 'technical' | 'behavioral') => SkillWeightInference
  competenciesPanelExpanded: boolean
  isFieldRequiredForWizard: (fieldName: string) => boolean
  onSetTechnicalSkills: (skills: TechnicalSkill[]) => void
  onSetBehavioralCompetencies: (comps: BehavioralCompetency[]) => void
  onExpandEditCompetencies: () => void
  onShowAddSkillModal: (category: 'language' | 'framework' | 'database' | 'tool' | 'general') => void
  onShowAddCompetencyModal: () => void
  onEditCompetency: (comp: BehavioralCompetency) => void

  // SalaryStage props
  salaryInfo: SalaryInfo
  salaryBenchmark: SalaryBenchmark | null
  isLoadingBenchmark: boolean
  salaryPanelExpanded: boolean
  onSalaryChange: (info: Partial<SalaryInfo>) => void
  onExpandEditSalary: () => void
  onShowAddBenefitModal: () => void

  // WSIQuestionsStage props
  wsiCandidates: WSIQuestionCandidate[]
  companyDefaultQuestions: CompanyDefaultQuestion[]
  isGeneratingWSI: boolean
  showCustomQuestionForm: boolean
  customQuestionText: string
  customQuestionType: 'open' | 'yes-no' | 'numeric' | 'multiple-choice'
  customQuestionRequired: boolean
  onSetCompanyDefaultQuestions: (questions: CompanyDefaultQuestion[]) => void
  onToggleQuestionSelection: (id: string) => void
  onDeleteQuestion: (id: string) => void
  onUpdateExpectedAnswer: (id: string, answer: string | number | boolean) => void
  onUpdateCorrectOption: (id: string, optionIndex: number) => void
  onGenerateWSIQuestions: (count: number, type: 'technical' | 'behavioral') => void
  onSetShowCustomQuestionForm: (show: boolean) => void
  onSetCustomQuestionText: (text: string) => void
  onSetCustomQuestionType: (type: 'open' | 'yes-no' | 'numeric' | 'multiple-choice') => void
  onSetCustomQuestionRequired: (required: boolean) => void
  onAddCustomQuestion: () => void

  // ReviewPublishStage props
  wsiQuestions: ReviewPublishStageProps['wsiQuestions']
  jobDescription: string
  isGeneratingDescription: boolean
  publishingPlatforms: PublishingPlatform[]
  jobConfig: JobConfig
  publishedJobId: string | null
  onGoToStage: React.Dispatch<React.SetStateAction<WizardStage>>
  onSetCompetenciesTab: (tab: 'technical' | 'behavioral') => void
  onSetPublishingPlatforms: (updater: (prev: PublishingPlatform[]) => PublishingPlatform[]) => void
  onSetJobConfig: (updater: (prev: JobConfig) => JobConfig) => void
  onSetDetectedCriteria: (updater: (prev: DetectedCriteria) => DetectedCriteria) => void
  onUpdateLanguages: (languages: { name: string; level: string }[]) => void
  onGenerateJobDescription: () => void

  // SearchCalibrationStage props
  searchPhase: SearchPhase
  calibrationCandidates: CalibrationCandidate[]
  calibrationComplete: boolean
  isLoadingCalibration: boolean
  hasAttemptedCalibrationGeneration: boolean
  approvedCandidates: string[]
  showCalibrationModal: boolean
  localCandidateCount: number
  globalCandidateCount: number
  globalSearchAuthorized: boolean
  preferredCandidateCount: number
  onSetPreferredCandidateCount: (count: number) => void
  onSetGlobalSearchAuthorized: (authorized: boolean) => void
  onSetSearchPhase: (phase: SearchPhase) => void
  onSetHasAttemptedCalibrationGeneration: (val: boolean) => void
  onSetCalibrationComplete: (val: boolean) => void
  onSetShowCalibrationModal: (val: boolean) => void
  onGenerateCalibrationCandidates: () => void
  onStartGlobalSearch: () => void
  onJobCreated?: () => void
  onClose: () => void

  // Navigation callbacks
  onResizeStart: () => void
  onPanelClose: () => void
  onFullscreenChange: (val: boolean) => void
  onClearDraft: () => void
  onGoToNextStage: () => void
  onGoToPreviousStage: () => void
  onPublishJob: () => void
  canAdvanceToNextStage: () => boolean
}

// ─── Component ────────────────────────────────────────────────────────────────

export function WizardRightPanel({
  // Layout
  panelWidth,
  resizeRef,

  // Stage navigation
  currentStage,
  currentStageIndex,
  currentStageConfig,

  // Panel state
  stageTransition,
  isFullscreen,
  catalogStatus,

  // Auto-save
  isAutoSaving,
  autoSaveLastSaved,
  hasPendingChanges,
  hasRestoredDraft,
  getLastSavedText,

  // WSI quality gates
  wsiQualityGates,

  // InputEvaluationStage props
  configLoaded,
  hasConfigData,
  criteriaItems,
  isHighlighted,
  hasFastTrackSuggestions,
  fastTrackIsLoading,
  fastTrackSuggestions,
  fastTrackSelectedJob,
  fastTrackSuggestionsShownTracked,
  onFastTrackSelectJob,
  onFastTrackDismiss,

  // EnrichedJDStage props
  enrichedJDData,
  isLoadingEnrichment,
  detectedCriteria,
  onAcceptEnrichedSuggestion,
  onRejectEnrichedSuggestion,
  onAcceptAllEnrichedSuggestions,

  // CompetenciesStage props
  technicalSkills,
  behavioralCompetencies,
  highlightedFields,
  basicInfoFields,
  companyConfig,
  inferSkillWeight,
  competenciesPanelExpanded,
  isFieldRequiredForWizard,
  onSetTechnicalSkills,
  onSetBehavioralCompetencies,
  onExpandEditCompetencies,
  onShowAddSkillModal,
  onShowAddCompetencyModal,
  onEditCompetency,

  // SalaryStage props
  salaryInfo,
  salaryBenchmark,
  isLoadingBenchmark,
  salaryPanelExpanded,
  onSalaryChange,
  onExpandEditSalary,
  onShowAddBenefitModal,

  // WSIQuestionsStage props
  wsiCandidates,
  companyDefaultQuestions,
  isGeneratingWSI,
  showCustomQuestionForm,
  customQuestionText,
  customQuestionType,
  customQuestionRequired,
  onSetCompanyDefaultQuestions,
  onToggleQuestionSelection,
  onDeleteQuestion,
  onUpdateExpectedAnswer,
  onUpdateCorrectOption,
  onGenerateWSIQuestions,
  onSetShowCustomQuestionForm,
  onSetCustomQuestionText,
  onSetCustomQuestionType,
  onSetCustomQuestionRequired,
  onAddCustomQuestion,

  // ReviewPublishStage props
  wsiQuestions,
  jobDescription,
  isGeneratingDescription,
  publishingPlatforms,
  jobConfig,
  publishedJobId,
  onGoToStage,
  onSetCompetenciesTab,
  onSetPublishingPlatforms,
  onSetJobConfig,
  onSetDetectedCriteria,
  onUpdateLanguages,
  onGenerateJobDescription,

  // SearchCalibrationStage props
  searchPhase,
  calibrationCandidates,
  calibrationComplete,
  isLoadingCalibration,
  hasAttemptedCalibrationGeneration,
  approvedCandidates,
  showCalibrationModal,
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

  // Navigation callbacks
  onResizeStart,
  onPanelClose,
  onFullscreenChange,
  onClearDraft,
  onGoToNextStage,
  onGoToPreviousStage,
  onPublishJob,
  canAdvanceToNextStage,
}: WizardRightPanelProps) {
  return (
    <div
      ref={resizeRef}
      className="flex flex-col rounded-md flex-shrink-0 m-3 ml-0 relative bg-lia-bg-secondary border border-lia-border-subtle"
      style={{width: `${panelWidth}%`}}
    >
      {/* Resize Handle - cursor change only, no visual indicator */}
      <div
        className="absolute left-0 top-0 bottom-0 w-2 cursor-col-resize z-10"
        onMouseDown={(e) => {
          e.preventDefault()
          onResizeStart()
        }}
      />

      {/* Panel Header with Stage Info */}
      <WizardHeader
        currentStageConfig={currentStageConfig!}
        currentStageIndex={currentStageIndex}
        catalogStatus={catalogStatus}
        isAutoSaving={isAutoSaving}
        autoSaveLastSaved={autoSaveLastSaved}
        hasPendingChanges={hasPendingChanges}
        hasRestoredDraft={hasRestoredDraft}
        isFullscreen={isFullscreen}
        onFullscreenChange={onFullscreenChange}
        onPanelClose={onPanelClose}
        onClearDraft={onClearDraft}
        getLastSavedText={getLastSavedText}
      />

      {/* WSI Quality Bar - visible in competencies and wsi-questions stages */}
      {(currentStage === 'competencies' || currentStage === 'wsi-questions') && (
        <div className="px-3 pb-2">
          <WSIQualityBar
            score={wsiQualityGates.score}
            fields={wsiQualityGates.fields}
            summaryText={wsiQualityGates.summaryText}
            scoreColor={wsiQualityGates.scoreColor}
            canAdvance={wsiQualityGates.canAdvance}
          />
        </div>
      )}

      <div className="flex-1 overflow-y-auto p-4 relative">
        {/* Loading Overlay during stage transitions */}
        {stageTransition === 'loading' && (
          <div className="absolute inset-0 bg-lia-bg-primary/90/90 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-4">
            <div className="relative">
              <div className="w-12 h-12 rounded-full border-3 border-lia-border-default border-t-lia-border-default animate-spin motion-reduce:animate-none" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Brain className="w-5 h-5 text-chat-cyan" />
              </div>
            </div>
            <div className="text-center">
              <p className="text-sm font-medium text-lia-text-secondary">
                LIA está analisando...
              </p>
              <p className="text-xs text-lia-text-tertiary mt-1">
                Preparando sugestões personalizadas
              </p>
            </div>
          </div>
        )}

        {/* Stage 1: Input Evaluation - Proactive Analysis */}
        {currentStage === 'input-evaluation' && (
          <InputEvaluationStage
            configLoaded={configLoaded}
            hasConfigData={hasConfigData}
            criteriaItems={criteriaItems}
            isHighlighted={isHighlighted}
            hasFastTrackSuggestions={hasFastTrackSuggestions}
            fastTrackIsLoading={fastTrackIsLoading}
            fastTrackSuggestions={fastTrackSuggestions}
            fastTrackSelectedJob={fastTrackSelectedJob}
            fastTrackSuggestionsShownTracked={fastTrackSuggestionsShownTracked}
            onFastTrackSelectJob={onFastTrackSelectJob}
            onFastTrackDismiss={onFastTrackDismiss}
          />
        )}

        {/* Stage: JD Enrichment - AI-powered suggestions */}
        {currentStage === 'jd-enrichment' && (
          <EnrichedJDStage
            enrichedData={enrichedJDData}
            onAcceptSuggestion={onAcceptEnrichedSuggestion}
            onRejectSuggestion={onRejectEnrichedSuggestion}
            onAcceptAll={onAcceptAllEnrichedSuggestions}
            isLoading={isLoadingEnrichment}
            detectedCriteria={{
              cargo: detectedCriteria.cargo ?? undefined,
              senioridade: detectedCriteria.senioridadeIdiomas ?? undefined,
              departamento: detectedCriteria.departamento ?? undefined,
              responsabilidades: detectedCriteria.responsabilidades,
              competenciasTecnicas: detectedCriteria.competenciasTecnicas,
              competenciasComportamentais: detectedCriteria.competenciasComportamentais,
            }}
          />
        )}

        {/* Stage 2: Competencies (Technical + Behavioral) - Unified Layout */}
        {currentStage === 'competencies' && (
          <CompetenciesStage
            technicalSkills={technicalSkills}
            behavioralCompetencies={behavioralCompetencies}
            highlightedFields={highlightedFields}
            onSetTechnicalSkills={onSetTechnicalSkills}
            onSetBehavioralCompetencies={onSetBehavioralCompetencies}
            basicInfoFields={basicInfoFields}
            // @ts-ignore TODO: fix type — Type 'import("/home/runner/workspace/plataforma-lia/src/components/expanded-chat
            detectedCriteria={detectedCriteria}
            companyConfig={companyConfig}
            inferSkillWeight={inferSkillWeight}
            isCollapsed={!competenciesPanelExpanded}
            onExpandEdit={onExpandEditCompetencies}
            isFieldRequired={isFieldRequiredForWizard('competencias')}
            onShowAddSkillModal={onShowAddSkillModal}
            onShowAddCompetencyModal={onShowAddCompetencyModal}
            onEditCompetency={onEditCompetency}
          />
        )}

        {/* Stage 5: Salary and Benefits */}
        {currentStage === 'salary' && (
          <SalaryStage
            salaryInfo={salaryInfo}
            highlightedFields={highlightedFields}
            onSalaryChange={onSalaryChange}
            salaryBenchmark={salaryBenchmark}
            isLoadingBenchmark={isLoadingBenchmark}
            companyConfig={companyConfig}
            isCollapsed={!salaryPanelExpanded}
            onExpandEdit={onExpandEditSalary}
            isFieldRequired={isFieldRequiredForWizard('salario')}
            onShowAddBenefitModal={onShowAddBenefitModal}
          />
        )}

        {/* Stage 6: WSI Screening Questions */}
        {currentStage === 'wsi-questions' && (
          <WSIQuestionsStage
            wsiCandidates={wsiCandidates}
            highlightedFields={highlightedFields}
            companyDefaultQuestions={companyDefaultQuestions}
            onSetCompanyDefaultQuestions={onSetCompanyDefaultQuestions}
            onToggleQuestionSelection={onToggleQuestionSelection}
            onDeleteQuestion={onDeleteQuestion}
            onUpdateExpectedAnswer={onUpdateExpectedAnswer}
            onUpdateCorrectOption={onUpdateCorrectOption}
            isGeneratingWSI={isGeneratingWSI}
            onGenerateWSIQuestions={onGenerateWSIQuestions}
            showCustomQuestionForm={showCustomQuestionForm}
            onSetShowCustomQuestionForm={onSetShowCustomQuestionForm}
            customQuestionText={customQuestionText}
            onSetCustomQuestionText={onSetCustomQuestionText}
            customQuestionType={customQuestionType}
            onSetCustomQuestionType={onSetCustomQuestionType}
            customQuestionRequired={customQuestionRequired}
            onSetCustomQuestionRequired={onSetCustomQuestionRequired}
            onAddCustomQuestion={onAddCustomQuestion}
          />
        )}

        {/* Stage 6: Review and Publish (Unified) */}
        {currentStage === 'review-publish' && (
          <ReviewPublishStage
            basicInfoFields={basicInfoFields}
            technicalSkills={technicalSkills}
            behavioralCompetencies={behavioralCompetencies}
            salaryInfo={salaryInfo}
            wsiQuestions={wsiQuestions}
            jobDescription={jobDescription}
            isGeneratingDescription={isGeneratingDescription}
            companyConfig={companyConfig}
            publishingPlatforms={publishingPlatforms}
            jobConfig={jobConfig}
            detectedCriteria={detectedCriteria}
            publishedJobId={publishedJobId}
            onGoToStage={onGoToStage}
            onSetCompetenciesTab={onSetCompetenciesTab}
            onSetPublishingPlatforms={onSetPublishingPlatforms}
            onSetJobConfig={onSetJobConfig}
            onSetDetectedCriteria={onSetDetectedCriteria}
            onUpdateLanguages={onUpdateLanguages}
            onGenerateJobDescription={onGenerateJobDescription}
          />
        )}

        {/* Stage 7: Search and Calibration (Unified) */}
        {currentStage === 'search-calibration' && (
          <SearchCalibrationStage
            searchPhase={searchPhase}
            calibrationCandidates={calibrationCandidates}
            calibrationComplete={calibrationComplete}
            isLoadingCalibration={isLoadingCalibration}
            hasAttemptedCalibrationGeneration={hasAttemptedCalibrationGeneration}
            approvedCandidates={approvedCandidates}
            showCalibrationModal={showCalibrationModal}
            publishedJobId={publishedJobId}
            localCandidateCount={localCandidateCount}
            globalCandidateCount={globalCandidateCount}
            globalSearchAuthorized={globalSearchAuthorized}
            preferredCandidateCount={preferredCandidateCount}
            onSetPreferredCandidateCount={onSetPreferredCandidateCount}
            onSetGlobalSearchAuthorized={onSetGlobalSearchAuthorized}
            onSetSearchPhase={onSetSearchPhase}
            onSetHasAttemptedCalibrationGeneration={onSetHasAttemptedCalibrationGeneration}
            onSetCalibrationComplete={onSetCalibrationComplete}
            onSetShowCalibrationModal={onSetShowCalibrationModal}
            onGenerateCalibrationCandidates={onGenerateCalibrationCandidates}
            onStartGlobalSearch={onStartGlobalSearch}
            onJobCreated={onJobCreated}
            onClose={onClose}
          />
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="px-4 py-3 bg-lia-bg-primary rounded-b-md">
        {currentStage === 'search-calibration' ? (
          <SearchCalibrationNavButtons
            calibrationCandidates={calibrationCandidates}
            calibrationComplete={calibrationComplete}
            isLoadingCalibration={isLoadingCalibration}
            hasAttemptedCalibrationGeneration={hasAttemptedCalibrationGeneration}
            approvedCandidates={approvedCandidates}
            onSetShowCalibrationModal={onSetShowCalibrationModal}
          />
        ) : currentStage === 'input-evaluation' ? (
          <div className="text-center text-micro text-lia-text-tertiary">
            Continue descrevendo a vaga para detectar mais critérios
          </div>
        ) : currentStage === 'jd-enrichment' ? (
          <div className="text-center text-micro text-lia-text-tertiary">
            Revise as sugestões no chat e responda o que deseja aceitar ou modificar
          </div>
        ) : (
          <div className="flex gap-2">
            {currentStageIndex > 0 && (
              <Button
                variant="outline"
                className="flex-1 h-9 rounded-md text-xs font-medium border-lia-border-subtle text-lia-text-secondary hover:border-lia-btn-primary-bg hover:text-lia-text-primary"
                onClick={onGoToPreviousStage}
                aria-label="Voltar para etapa anterior"
              >
                <ChevronLeft className="w-3.5 h-3.5 mr-1" />
                Voltar
              </Button>
            )}
            {/* Hide confirmation button for conversational stages - flow is via chat, not buttons */}
            {currentStage !== 'salary' && currentStage !== 'competencies' && (
              <Button
                className={cn(
 "flex-1 h-9 rounded-md text-xs font-semibold transition-colors",
                  currentStageIndex === 0 ? "w-full" : "",
                  currentStage === 'review-publish'
                    ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                    : canAdvanceToNextStage()
                      ? "bg-lia-btn-primary-bg text-lia-btn-primary-text"
                      : "bg-lia-interactive-active text-lia-text-disabled"
                )}
                disabled={!canAdvanceToNextStage()}
                onClick={currentStage === 'review-publish' ? onPublishJob : onGoToNextStage}
                aria-label={currentStage === 'review-publish' ? 'Publicar vaga' : 'Confirmar etapa atual'}
              >
                {(() => {
                  const stage = currentStage as string
                  if (stage === 'review-publish') {
                    return (
                      <>
                        <Rocket className="w-3.5 h-3.5 mr-1.5" />
                        Publicar Vaga
                      </>
                    )
                  }
                  if (stage === 'wsi-questions') {
                    return (
                      <>
                        <Check className="w-3.5 h-3.5 mr-1" />
                        Confirmar Triagem
                      </>
                    )
                  }
                  if (stage === 'input-evaluation') {
                    return (
                      <>
                        <Check className="w-3.5 h-3.5 mr-1" />
                        Confirmar Avaliação
                      </>
                    )
                  }
                  return (
                    <>
                      <Check className="w-3.5 h-3.5 mr-1" />
                      Confirmar
                    </>
                  )
                })()}
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
