"use client"

import { useCandidatePreviewCore } from"@/components/candidate-preview/useCandidatePreviewCore"
import { Chip } from "@/components/ui/chip"
import { Activity, FileText, Brain, UserCheck } from"lucide-react"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from"@/components/ui/tooltip"
import { CandidatePreviewHeader } from"@/components/candidate-preview/CandidatePreviewHeader"
import { CandidatePreviewActionBar } from"@/components/candidate-preview/CandidatePreviewActionBar"
import { PipelineDecisionBar } from"@/components/candidate-preview/PipelineDecisionBar"
import { CandidatePreviewModals } from"@/components/candidate-preview/CandidatePreviewModals"
import { CandidateFilesTab } from"@/components/candidate-preview/CandidateFilesTab"
import { CandidateActivitiesTab } from"@/components/candidate-preview/CandidateActivitiesTab"
import { CandidatePreviewProfileTab } from"@/components/candidate-preview/CandidatePreviewProfileTab"
import { CandidateOpinionsTab } from"@/components/candidate-preview/CandidateOpinionsTab"
import type { CandidateData } from"@/components/candidate-preview/ProfileTabTypes"

interface CandidatePreviewProps {
  candidate: Record<string, unknown>
  isOpen: boolean
  onClose: () => void
  isMaximized?: boolean
  onToggleMaximize?: () => void
  candidates?: Record<string, unknown>[]
  currentIndex?: number
  onNavigateCandidate?: (index: number) => void
  onOpenFullPage?: (candidate: Record<string, unknown>) => void
  onScheduleInterview?: (candidate: Record<string, unknown>) => void
  onAddToVacancy?: (candidate: Record<string, unknown>) => void
  onToggleFavorite?: (candidateId: string) => void
  onWSIScreening?: (candidate: Record<string, unknown>) => void
  onOpenTriagemDetails?: (candidate: Record<string, unknown>) => void
  isFavorite?: boolean
  onSendEmail?: (candidate: Record<string, unknown>) => void
  onSendWhatsApp?: (candidate: Record<string, unknown>) => void  
  onSendTriagem?: (candidate: Record<string, unknown>) => void
  onSendAgendamento?: (candidate: Record<string, unknown>) => void
  onSendFeedback?: (candidate: Record<string, unknown>) => void
  onContact?: (candidate: Record<string, unknown>, channel?: 'email' | 'whatsapp') => void
  onSchedule?: (candidate: Record<string, unknown>) => void
  onAddToList?: (candidate: Record<string, unknown>) => void
  jobId?: string
  searchCriteria?: Record<string, unknown> | null
  onCandidateUpdated?: () => void
}

export function CandidatePreview({
  candidate,
  isOpen,
  onClose,
  isMaximized = false,
  onToggleMaximize,
  candidates = [],
  currentIndex = 0,
  onNavigateCandidate,
  onOpenFullPage,
  onScheduleInterview,
  onAddToVacancy,
  onToggleFavorite,
  onWSIScreening,
  onOpenTriagemDetails,
  isFavorite = false,
  onSendEmail,
  onSendWhatsApp,
  onSendTriagem,
  onSendAgendamento,
  onSendFeedback,
  onContact,
  onSchedule,
  onAddToList,
  jobId,
  searchCriteria,
  onCandidateUpdated,
}: CandidatePreviewProps) {
  const core = useCandidatePreviewCore(candidate, jobId)
  const {
    activeTab, setActiveTab,
    showLiaModal, setShowLiaModal,
    liaConversation, setLiaConversation,
    selectedFile, setSelectedFile,
    showPreview, setShowPreview,
    previewType, setPreviewType,
    isAnalyzingWithLia,
    lastAnalysisDate,
    liaChatMessages,
    isLiaChatLoading,
    opinionsData,
    isLoadingOpinions,
    expandedOpinionId, setExpandedOpinionId,
    opinionsHistory,
    isLoadingHistory,
    isErrorHistory, retryOpinionsHistory,
    showUpdateOpinionAlert, setShowUpdateOpinionAlert,
    showInsufficientDataModal, setShowInsufficientDataModal,
    dataRequirements,
    lastOpinionDate,
    screeningModalOpen, setScreeningModalOpen,
    screeningModalData, setScreeningModalData,
    discModalOpen, setDiscModalOpen,
    discModalData, setDiscModalData,
    bigFiveModalOpen, setBigFiveModalOpen,
    bigFiveModalCandidate, setBigFiveModalCandidate,
    copiedItemId,
    sendLiaMessage,
    generateNewOpinion,
    handleAnalyzeWithLia,
    handleProceedWithLimitedData,
    formatAnalysisDate,
    generateShortId,
    cleanTextForCopy,
    handleCopyOpinion,
    formatCurrency,
    getLanguagesData,
    hasSalaryData,
    hasAddressData,
    getAddressString,
    hasAdditionalDetails,
  } = core

  if (!isOpen || !candidate) return null

  candidate = {
    ...candidate,
    education: Array.isArray(candidate.education) ? candidate.education : (candidate.education ? [candidate.education] : []),
    workHistory: Array.isArray(candidate.work_history) ? candidate.work_history : (candidate.work_history ? [candidate.work_history] : []),
    skills: Array.isArray(candidate.skills) ? candidate.skills : (candidate.skills ? [candidate.skills] : []),
    certifications: Array.isArray(candidate.certifications) ? candidate.certifications : (candidate.certifications ? [candidate.certifications] : []),
    projects: Array.isArray(candidate.projects) ? candidate.projects : (candidate.projects ? [candidate.projects] : []),
    awards: Array.isArray(candidate.awards) ? candidate.awards : (candidate.awards ? [candidate.awards] : []),
  }

  const c = candidate as unknown as CandidateData
  const languagesData = getLanguagesData()

  const tabs = [
    { id: 'profile', label: 'Perfil Completo', icon: UserCheck },
    { id: 'activities', label: 'Atividades', icon: Activity },
    { id: 'files', label: 'Arquivos', icon: FileText },
    { id: 'opinions', label: 'Pareceres e Análises', icon: Brain, badge: ((opinionsData as unknown as {total_opinions?: number} | undefined)?.total_opinions || 0) }
  ]

  const liaActions = [
    { id: 'auto-contact', title: 'Contato Automático', icon: '📧', buttonText: 'Enviar convite para conversa' },
    { id: 'add-to-job', title: 'Adicionar à Vaga', icon: '🎯', buttonText: 'Adicionar ao processo seletivo' },
    { id: 'schedule-interview', title: 'Agendar Entrevista', icon: '📅', buttonText: 'Sugerir horários disponíveis' },
    { id: 'request-portfolio', title: 'Solicitar Portfólio', icon: '📂', buttonText: 'Enviar solicitação automática' },
    { id: 'reference-check', title: 'Verificar Referências', icon: '✅', buttonText: 'Iniciar verificação' },
    { id: 'salary-analysis', title: 'Análise Salarial', icon: '💰', buttonText: 'Gerar relatório salarial' }
  ]

  return (
    <div className="h-full bg-lia-bg-primary dark:bg-lia-bg-primary border border-lia-border-subtle dark:border-lia-border-subtle flex flex-col transition-[width,height] duration-300 w-full">
      <TooltipProvider delayDuration={200}>
        <div className="p-3 dark:border-lia-border-subtle bg-lia-bg-primary dark:bg-lia-bg-primary">
          <CandidatePreviewHeader
            c={c}
            candidate={candidate}
            generateShortId={generateShortId}
            onOpenFullPage={onOpenFullPage}
            onClose={onClose}
          />
          <CandidatePreviewActionBar
            c={c}
            candidate={candidate}
            onSendEmail={onSendEmail}
            onSendWhatsApp={onSendWhatsApp}
            onSendAgendamento={onSendAgendamento}
            onScheduleInterview={onScheduleInterview}
            onWSIScreening={onWSIScreening}
            onSendTriagem={onSendTriagem}
            onAddToVacancy={onAddToVacancy}
            onToggleFavorite={onToggleFavorite}
            onSendFeedback={onSendFeedback}
            isFavorite={isFavorite}
          />
        </div>
      </TooltipProvider>

      {!!(jobId || c.vacancy_id || c.vacancy_candidate_id) && (
        <PipelineDecisionBar
          candidate={c}
          jobId={jobId}
          onCandidateUpdated={onCandidateUpdated}
        />
      )}

      <div className="dark:border-lia-border-subtle flex items-center">
        <div className="flex overflow-x-auto">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'activities' | 'profile' | 'files' | 'opinions')}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium whitespace-nowrap transition-colors motion-reduce:transition-none ${
 activeTab === tab.id
                  ? 'rounded-lg bg-lia-bg-tertiary text-lia-text-primary font-semibold'
                  : 'text-lia-text-secondary hover:text-lia-text-primary'
              }`}
            >
              <tab.icon className="w-3 h-3" />
              {tab.label}
              {'badge' in tab && tab.badge! > 0 && (
                <Chip variant="neutral" muted className="text-micro px-1 py-0 h-4 ml-1 bg-wedo-cyan/15">
                  {tab.badge}
                </Chip>
              )}
            </button>
          ))}
        </div>
      </div>

      <TooltipProvider delayDuration={200}>
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'profile' && (
          <CandidatePreviewProfileTab
            candidate={c as Record<string, unknown>}
            jobId={jobId}
            opinionsData={opinionsData}
            isLoadingOpinions={isLoadingOpinions}
            isAnalyzingWithLia={isAnalyzingWithLia}
            lastAnalysisDate={lastAnalysisDate}
            formatAnalysisDate={formatAnalysisDate}
            handleAnalyzeWithLia={handleAnalyzeWithLia}
            formatCurrency={formatCurrency}
            languagesData={languagesData}
            hasSalaryData={hasSalaryData}
            hasAddressData={hasAddressData}
            getAddressString={getAddressString}
            searchCriteria={searchCriteria}
          />
        )}

        {activeTab === 'activities' && (
          <CandidateActivitiesTab
            candidate={c}
            jobId={jobId}
            onShowLiaModal={() => setShowLiaModal(true)}
            onOpenTriagemDetails={onOpenTriagemDetails}
            onSetScreeningModalData={setScreeningModalData}
            onSetScreeningModalOpen={setScreeningModalOpen}
            onSetDiscModalData={setDiscModalData}
            onSetDiscModalOpen={setDiscModalOpen}
            onSetBigFiveModalCandidate={setBigFiveModalCandidate}
            onSetBigFiveModalOpen={setBigFiveModalOpen}
            onSetSelectedFile={setSelectedFile}
            onSetPreviewType={setPreviewType}
            onSetShowPreview={setShowPreview}
          />
        )}

        {activeTab === 'files' && (
          <CandidateFilesTab
            candidate={c}
          />
        )}

        {activeTab === 'opinions' && (
          <CandidateOpinionsTab
            opinionsHistory={opinionsHistory}
            isLoadingHistory={isLoadingHistory}
            isErrorHistory={isErrorHistory}
            onRetryHistory={retryOpinionsHistory}
            expandedOpinionId={expandedOpinionId as never}
            setExpandedOpinionId={setExpandedOpinionId as never}
            copiedItemId={copiedItemId}
            handleCopyOpinion={handleCopyOpinion as never}
          />
        )}
      </div>

      <CandidatePreviewModals
        c={c}
        candidate={candidate}
        showLiaModal={showLiaModal}
        setShowLiaModal={setShowLiaModal}
        liaActions={liaActions}
        liaChatMessages={liaChatMessages as never}
        isLiaChatLoading={isLiaChatLoading}
        liaConversation={liaConversation}
        setLiaConversation={setLiaConversation}
        sendLiaMessage={sendLiaMessage}
        onContact={onContact}
        onSendEmail={onSendEmail}
        onSchedule={onSchedule}
        onScheduleInterview={onScheduleInterview}
        onSendAgendamento={onSendAgendamento}
        onAddToList={onAddToList}
        onAddToVacancy={onAddToVacancy}
        showUpdateOpinionAlert={showUpdateOpinionAlert}
        setShowUpdateOpinionAlert={setShowUpdateOpinionAlert}
        lastOpinionDate={lastOpinionDate}
        generateNewOpinion={generateNewOpinion}
        showInsufficientDataModal={showInsufficientDataModal}
        setShowInsufficientDataModal={setShowInsufficientDataModal}
        dataRequirements={dataRequirements}
        handleProceedWithLimitedData={handleProceedWithLimitedData}
        screeningModalOpen={screeningModalOpen}
        setScreeningModalOpen={setScreeningModalOpen}
        screeningModalData={screeningModalData as never}
        setScreeningModalData={setScreeningModalData as never}
        onOpenTriagemDetails={onOpenTriagemDetails}
        discModalOpen={discModalOpen}
        setDiscModalOpen={setDiscModalOpen}
        discModalData={discModalData}
        setDiscModalData={setDiscModalData}
        bigFiveModalOpen={bigFiveModalOpen}
        setBigFiveModalOpen={setBigFiveModalOpen}
        bigFiveModalCandidate={bigFiveModalCandidate}
        setBigFiveModalCandidate={setBigFiveModalCandidate}
      />
      
      </TooltipProvider>
    </div>
  )
}
