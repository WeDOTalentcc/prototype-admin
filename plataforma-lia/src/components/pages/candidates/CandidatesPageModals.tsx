"use client"

const BatchApprovalModal = dynamic(() => import("@/components/batch-approval-modal").then(m => ({ default: m.BatchApprovalModal })), { ssr: false, loading: () => null })
const RubricEvaluationModal = dynamic(() => import("@/components/rubric-evaluation-modal").then(m => ({ default: m.RubricEvaluationModal })), { ssr: false, loading: () => null })
const ContactModal = dynamic(() => import("@/components/quick-actions-modals").then(m => ({ default: m.ContactModal })), { ssr: false, loading: () => null })
const ScheduleModal = dynamic(() => import("@/components/quick-actions-modals").then(m => ({ default: m.ScheduleModal })), { ssr: false, loading: () => null })
import { GlobalExpansionConfirmModal } from "@/components/pages/candidates/GlobalExpansionConfirmModal"
import { SourceChangeConfirmModal } from "@/components/pages/candidates/SourceChangeConfirmModal"
import { ContactFilterConfirmModal } from "@/components/pages/candidates/ContactFilterConfirmModal"
import { DeleteArchetypeModal } from "@/components/pages/candidates/DeleteArchetypeModal"
import type { CommunicationType } from "@/components/modals/unified-communication-modal"
const UnifiedCommunicationModal = dynamic(() => import("@/components/modals/unified-communication-modal").then(m => ({ default: m.UnifiedCommunicationModal })), { ssr: false, loading: () => null })
const CandidateComparison = dynamic(() => import("@/components/candidate-comparison").then(m => ({ default: m.CandidateComparison })), { ssr: false, loading: () => null })
const AddToListModal = dynamic(() => import("@/components/modals/add-to-list-modal").then(m => ({ default: m.AddToListModal })), { ssr: false, loading: () => null })
const ShareSearchModal = dynamic(() => import("@/components/modals/share-search-modal").then(m => ({ default: m.ShareSearchModal })), { ssr: false, loading: () => null })
const AddCandidatesToVacancyModal = dynamic(() => import("@/components/modals/add-candidates-to-vacancy-modal").then(m => ({ default: m.AddCandidatesToVacancyModal })), { ssr: false, loading: () => null })
const AddListToVacanciesModal = dynamic(() => import("@/components/modals/add-list-to-vacancies-modal").then(m => ({ default: m.AddListToVacanciesModal })), { ssr: false, loading: () => null })
import { UnsavedPearchWarningModal } from "@/components/modals/unsaved-pearch-warning-modal"
const WSITextScreeningModal = dynamic(() => import("@/components/wsi").then(m => ({ default: m.WSITextScreeningModal })), { ssr: false, loading: () => null })
const WSIVoiceScreeningStatus = dynamic(() => import("@/components/wsi").then(m => ({ default: m.WSIVoiceScreeningStatus })), { ssr: false, loading: () => null })
const WSIScorecard = dynamic(() => import("@/components/wsi").then(m => ({ default: m.WSIScorecard })), { ssr: false, loading: () => null })
const WSITriagemInviteModal = dynamic(() => import("@/components/wsi/wsi-triagem-invite-modal").then(m => ({ default: m.WSITriagemInviteModal })), { ssr: false, loading: () => null })
const SendEmailModal = dynamic(() => import("@/components/email-templates").then(m => ({ default: m.SendEmailModal })), { ssr: false, loading: () => null })
import type { ParsedCVResponse } from "@/components/cv"
const CVPreview = dynamic(() => import("@/components/cv").then(m => ({ default: m.CVPreview })), { ssr: false, loading: () => null })
const RevealCreditsModal = dynamic(() => import("@/components/reveal-credits-modal").then(m => ({ default: m.RevealCreditsModal })), { ssr: false, loading: () => null })
import { CreditConfirmationModal } from "@/components/pages/candidates/CreditConfirmationModal"
import { SaveAsArchetypeModal } from "@/components/pages/candidates/SaveAsArchetypeModal"
import { EditQueryModal } from "@/components/pages/candidates/EditQueryModal"
import { PreviewSuggestionModal } from "@/components/pages/candidates/PreviewSuggestionModal"
import { liaApi } from "@/services/lia-api"
import dynamic from "next/dynamic"
import type { Candidate } from "@/components/pages/candidates/types"

const NewCandidateUnifiedModal = dynamic(() => import("@/components/modals/new-candidate-unified-modal").then(m => ({ default: m.NewCandidateUnifiedModal })), {
  ssr: false,
  loading: () => null,
})
const CandidatePage = dynamic(() => import("@/components/candidate-page").then(m => ({ default: m.CandidatePage })), { ssr: false })
const AdvancedFiltersModal = dynamic(() => import("@/components/search/advanced-filters-modal").then(m => ({ default: m.AdvancedFiltersModal })), { ssr: false })

import type { CandidatesPageModalsProps } from "./CandidatesPageModals.types"
export function CandidatesPageModals({
  selectedCandidateForAction,
  contactModalCandidate,
  showContactModal,
  contactModalAction,
  setShowContactModal,
  setSelectedCandidateForAction,
  setContactModalCandidate,
  setContactModalAction,
  handleSendMessage,
  showScheduleModal,
  setShowScheduleModal,
  handleScheduleComplete,
  unifiedModalOpen,
  unifiedModalCandidate,
  unifiedModalType,
  lastSearchQuery,
  handleUnifiedModalClose,
  handleUnifiedModalSend,
  showComparisonModal,
  setShowComparisonModal,
  selectedCandidatesForBatch,
  sortedCandidates,
  candidates,
  handleNavigateToFullProfile,
  handleScheduleInterview,
  handleContactCandidate,
  showCandidatePage,
  selectedCandidate,
  handleCloseCandidatePage,
  showAddCandidateModal,
  setShowAddCandidateModal,
  preSelectedListForModal,
  setPreSelectedListForModal,
  handleAddCandidate,
  setCandidateListsForModal,
  bulkJobVacancies,
  candidateListsForModal,
  handleCandidatePageOpen,
  showBatchApproval,
  setShowBatchApproval,
  convertCandidatesForBatch,
  handleBatchApprovalComplete,
  wsiCandidateForScreening,
  setWsiCandidateForScreening,
  showWSITextModal,
  setShowWSITextModal,
  showWSIVoiceModal,
  setShowWSIVoiceModal,
  handleWSIScreeningComplete,
  showWSIInviteModal,
  setShowWSIInviteModal,
  wsiInviteCandidate,
  setWsiInviteCandidate,
  showRubricModal,
  setShowRubricModal,
  rubricCandidate,
  setRubricCandidate,
  rubricEvaluationData,
  setRubricEvaluationData,
  toast,
  showSendEmailModal,
  setShowSendEmailModal,
  emailCandidateSelected,
  setEmailCandidateSelected,
  showRevealModal,
  setShowRevealModal,
  revealCandidate,
  setRevealCandidate,
  handleRevealContact,
  revealType,
  showCVPreviewModal,
  setShowCVPreviewModal,
  parsedCVData,
  setParsedCVData,
  handleCVConfirmed,
  showCreditConfirmation,
  setShowCreditConfirmation,
  creditEstimate,
  pearchSearchOptions,
  setPearchSearchOptions,
  setPendingSearchRequest,
  handleConfirmPearchSearch,
  showGlobalExpansionConfirm,
  setShowGlobalExpansionConfirm,
  lastSuccessfulQuery,
  localResultsCount,
  isExpandingToGlobal,
  handleExpandToGlobal,
  showSourceChangeModal,
  setShowSourceChangeModal,
  pendingSourceChange,
  setPendingSourceChange,
  confirmSourceChange,
  showContactFilterModal,
  setShowContactFilterModal,
  pendingContactFilter,
  setPendingContactFilter,
  confirmContactFilterChange,
  showSaveAsArchetypeModal,
  setShowSaveAsArchetypeModal,
  searchResults,
  isCreatingArchetype,
  setIsCreatingArchetype,
  archetypeCreationStep,
  setArchetypeCreationStep,
  newArchetypeData,
  setNewArchetypeData,
  setUserArchetypes,
  setChatMessages,
  showAdvancedSearch,
  setShowAdvancedSearch,
  activeSearchFilters,
  setActiveSearchFilters,
  hideViewedCandidates,
  showAddToListModal,
  setShowAddToListModal,
  addToListCandidateIds,
  setAddToListCandidateIds,
  addToListCandidateNames,
  setAddToListCandidateNames,
  showShareSearchModal,
  setShowShareSearchModal,
  shareSearchTitle,
  setShareSearchTitle,
  shareSearchCandidates,
  setShareSearchCandidates,
  showAddListToVacanciesModal,
  setShowAddListToVacanciesModal,
  selectedListForVacancies,
  setSelectedListForVacancies,
  showAddToVacancyModal,
  setShowAddToVacancyModal,
  setSelectedCandidatesForBatch,
  user,
  showUnsavedWarningModal,
  setShowUnsavedWarningModal,
  setPendingTabChange,
  handleSaveAllAndExit,
  handleExitWithoutSaving,
  unsavedPearchCandidates,
  isSavingToBase,
  showEditQueryModal,
  setShowEditQueryModal,
  editQueryValue,
  getActiveSearchFiltersCount,
  searchSource,
  setSearchSource,
  setSearchTerm,
  setLastSearchQuery,
  setLastSearchMode,
  setLastSearchEntities,
  setLastSearchMetadata,
  executeSearch,
  previewSuggestion,
  setPreviewSuggestion,
  previewingUserArchetype,
  setPreviewingUserArchetype,
  buildFiltersFromTags,
  setLiaPromptValue,
  setActiveSearchTab,
  archetypeToDelete,
  setArchetypeToDelete,
}: CandidatesPageModalsProps) {
  return (
    <>
      {/* Contact Modal */}
      {(selectedCandidateForAction || contactModalCandidate) && (
        <ContactModal
          isOpen={showContactModal}
          onClose={() => {
            setShowContactModal(false)
            setSelectedCandidateForAction(null)
            setContactModalCandidate(null)
            setContactModalAction('general')
          }}
          candidate={(() => {
            const c = contactModalCandidate || selectedCandidateForAction
            if (!c) return null
            return {
              id: c.id,
              name: c.name,
              role: c.position || c.role || '',
              email: c.email,
              phone: c.phone,
              location: c.location,
              avatar: c.avatar,
              score: c.score || 0,
              status: c.status || 'Novo',
              matchPercentage: c.liaAnalysis?.score ?? c.score ?? 0,
              riskLevel: 'low' as const,
              culturalFit: 85,
              technicalMatch: 90,
              experience: String(c.experience || ''),
              seniority: c.seniority_level || 'Pleno',
              availability: 'Imediata',
              expectedSalary: c.salary?.expected ? String(c.salary.expected) : '',
              preferredLocation: c.location,
              linkedin: c.linkedin,
              skills: c.skills || [],
              lastActivity: new Date().toISOString(),
              source: 'internal'
            }
          })()}
          onSend={handleSendMessage}
          initialAction={contactModalAction}
        />
      )}

      {/* Schedule Modal */}
      {selectedCandidateForAction && (
        <ScheduleModal
          isOpen={showScheduleModal}
          onClose={() => {
            setShowScheduleModal(false)
            setSelectedCandidateForAction(null)
          }}
          // @ts-ignore TODO: fix type
          candidate={(() => {
            const sca = selectedCandidateForAction
            return ({
            id: sca.id,
            name: sca.name,
            role: sca.position,
            email: sca.email,
            phone: sca.phone,
            location: sca.location,
            avatar: sca.avatar,
            score: sca.score,
            status: sca.status,
            matchPercentage: sca.liaAnalysis?.score ?? sca.score,
            riskLevel: 'low' as const,
            culturalFit: 85,
            technicalMatch: 90,
            experience: String(sca.experience),
            seniority: sca.seniority_level || 'Pleno',
            availability: 'Imediata',
            expectedSalary: sca.salary?.expected ? String(sca.salary.expected) : '',
            preferredLocation: sca.location,
            linkedin: sca.linkedin,
            skills: sca.skills,
            lastActivity: new Date().toISOString(),
            source: 'internal'
          })
          })()}
          onSchedule={handleScheduleComplete}
        />
      )}

      {/* Unified Communication Modal */}
      <UnifiedCommunicationModal
        isOpen={unifiedModalOpen}
        onClose={handleUnifiedModalClose}
        candidate={unifiedModalCandidate ? (() => {
          const umc = unifiedModalCandidate
          return {
            id: umc.id,
            name: umc.name,
            role: umc.position || umc.current_title || '',
            email: umc.email,
            phone: umc.phone,
            location: umc.location,
            avatar: umc.avatar,
            score: umc.score,
            matchPercentage: umc.liaAnalysis?.score ?? umc.score,
            skills: umc.skills
          }
        })() : null}
        type={unifiedModalType}
        jobTitle={lastSearchQuery || undefined}
        onSend={handleUnifiedModalSend}
        companyId="demo"
      />

      {/* Candidate Comparison Modal */}
      {showComparisonModal && selectedCandidatesForBatch.size >= 2 && (
        <CandidateComparison
          isOpen={showComparisonModal}
          onClose={() => setShowComparisonModal(false)}
          // @ts-ignore TODO: fix type
          candidates={sortedCandidates
            .filter(c => selectedCandidatesForBatch.has(c.id))
            .map(c => ({
              id: c.id,
              name: c.name,
              role: c.position,
              email: c.email,
              phone: c.phone,
              location: c.location,
              avatar: c.avatar,
              score: c.score,
              status: c.status,
              matchPercentage: c.liaAnalysis?.score ?? c.score,
              riskLevel: 'low' as const,
              culturalFit: 85,
              technicalMatch: 90,
              experience: String(c.experience),
              seniority: c.seniority_level || 'Pleno',
              availability: 'Imediata',
              expectedSalary: c.salary?.expected ? String(c.salary.expected) : '',
              skills: c.skills,
              lastActivity: new Date().toISOString(),
              source: 'internal'
            }))}
          onSelectCandidate={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleNavigateToFullProfile(candidate)
          }}
          onScheduleInterview={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleScheduleInterview(candidate)
          }}
          onContactCandidate={(candidateId) => {
            const candidate = candidates.find(c => c.id === candidateId)
            if (candidate) handleContactCandidate(candidate)
          }}
        />
      )}

      {/* Candidate Page Modal */}
      {showCandidatePage && selectedCandidate && (
        <CandidatePage
          // @ts-ignore TODO: fix type
          candidate={selectedCandidate}
          isOpen={showCandidatePage}
          onClose={handleCloseCandidatePage}
          onBackToKanban={() => {}}
        />
      )}

      {/* New Candidate Unified Modal */}
      <NewCandidateUnifiedModal
        key={`modal-${preSelectedListForModal?.id || 'default'}`}
        isOpen={showAddCandidateModal}
        onClose={() => {
          setShowAddCandidateModal(false)
          setPreSelectedListForModal(null)
        }}
        onCandidateAdded={(candidate) => {
          handleAddCandidate(candidate)
          if (preSelectedListForModal) {
            liaApi.getCandidateLists({ limit: 50 }).then(response => {
              if (response.items) {
                setCandidateListsForModal(response.items.map(list => ({
                  id: list.id,
                  name: list.name,
                  color: list.color
                })))
              }
            }).catch(() => {})
          }
        }}
        jobVacancies={bulkJobVacancies.map(j => ({ id: j.id, title: j.title, department: j.department, location: j.location }))}
        candidateLists={candidateListsForModal}
        preSelectedListId={preSelectedListForModal?.id}
        preSelectedListName={preSelectedListForModal?.name}
        onGoToSearch={() => {
          setShowAddCandidateModal(false)
          setPreSelectedListForModal(null)
        }}
        onOpenFullProfile={(candidateId) => {
          const candidate = candidates.find(c => c.id === candidateId)
          if (candidate) {
            handleCandidatePageOpen(candidate)
          }
        }}
      />

      {/* Batch Approval Modal */}
      {showBatchApproval && (
        <BatchApprovalModal
          // @ts-ignore TODO: fix type
          candidates={convertCandidatesForBatch(candidates.filter(c => selectedCandidatesForBatch.has(c.id)))}
          isOpen={showBatchApproval}
          onClose={() => setShowBatchApproval(false)}
          onApprovalComplete={handleBatchApprovalComplete}
        />
      )}

      {/* WSI Text Screening Modal */}
      {wsiCandidateForScreening && (
        <WSITextScreeningModal
          isOpen={showWSITextModal}
          onClose={() => {
            setShowWSITextModal(false)
            setWsiCandidateForScreening(null)
          }}
          candidate={{
            id: wsiCandidateForScreening.id,
            name: wsiCandidateForScreening.name,
            avatar: wsiCandidateForScreening.avatar,
            position: wsiCandidateForScreening.position
          }}
          jobVacancy={{
            id: 'default-vacancy',
            title: wsiCandidateForScreening.position || 'Vaga atual'
          }}
          onComplete={handleWSIScreeningComplete}
        />
      )}

      {/* WSI Voice Screening Modal */}
      {wsiCandidateForScreening && (
        <WSIVoiceScreeningStatus
          isOpen={showWSIVoiceModal}
          onClose={() => {
            setShowWSIVoiceModal(false)
            setWsiCandidateForScreening(null)
          }}
          candidate={{
            id: wsiCandidateForScreening.id,
            name: wsiCandidateForScreening.name,
            phone: wsiCandidateForScreening.phone
          }}
          jobVacancy={{
            id: 'default-vacancy',
            title: wsiCandidateForScreening.position || 'Vaga atual'
          }}
          onComplete={handleWSIScreeningComplete}
          autoStart={true}
        />
      )}

      {/* WSI Triagem Invite Modal */}
      <WSITriagemInviteModal
        isOpen={showWSIInviteModal}
        onClose={() => {
          setShowWSIInviteModal(false)
          setWsiInviteCandidate(null)
        }}
        candidate={wsiInviteCandidate ? {
          id: wsiInviteCandidate.id,
          name: wsiInviteCandidate.name,
          role: wsiInviteCandidate.position,
          email: wsiInviteCandidate.email,
          phone: wsiInviteCandidate.phone,
          location: wsiInviteCandidate.location,
          avatar: wsiInviteCandidate.avatar
        } : null}
        jobTitle={wsiInviteCandidate?.position || 'Vaga'}
        onSend={async (data) => {
          try {
            if (data.channel === 'email' && wsiInviteCandidate?.email) {
              const sendData = data as { subject?: string; message?: string; channel: string }
              await liaApi.sendEmail('wsi-triagem-invite', {
                recipient_email: wsiInviteCandidate.email,
                recipient_name: wsiInviteCandidate.name,
                candidate_id: wsiInviteCandidate.id,
                subject_override: sendData.subject || `Convite para Triagem - ${wsiInviteCandidate.position || 'Vaga'}`,
                body_override: sendData.message,
                variables: {
                  candidate_name: wsiInviteCandidate.name,
                  job_title: wsiInviteCandidate.position || 'Vaga'
                }
              })
            }
            setShowWSIInviteModal(false)
            setWsiInviteCandidate(null)
          } catch (error) {
            setShowWSIInviteModal(false)
            setWsiInviteCandidate(null)
          }
        }}
      />

      {/* Rubric Evaluation Modal */}
      <RubricEvaluationModal
        isOpen={showRubricModal}
        onClose={() => {
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
        evaluation={rubricEvaluationData}
        candidateId={rubricCandidate?.id || ''}
        candidateName={rubricCandidate?.name}
        jobId=""
        onApprove={async () => {
          toast({
            title: "Candidato aprovado",
            description: `${rubricCandidate?.name} foi aprovado com sucesso`
          })
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
        onReject={async () => {
          toast({
            title: "Candidato reprovado",
            description: `${rubricCandidate?.name} foi reprovado`
          })
          setShowRubricModal(false)
          setRubricCandidate(null)
          setRubricEvaluationData(null)
        }}
      />

      {/* Send Email Modal */}
      <SendEmailModal
        isOpen={showSendEmailModal}
        onClose={() => {
          setShowSendEmailModal(false)
          setEmailCandidateSelected(null)
        }}
        // @ts-ignore TODO: fix type
        candidate={emailCandidateSelected ? ({
          id: emailCandidateSelected.id,
          name: emailCandidateSelected.name,
          email: emailCandidateSelected.email,
          phone: emailCandidateSelected.phone,
          current_title: emailCandidateSelected.position,
          technical_skills: emailCandidateSelected.skills,
          source: 'internal',
          is_active: true,
          is_remote: emailCandidateSelected.workModel === 'remoto',
          willing_to_relocate: false,
          tags: emailCandidateSelected.tags,
          status: emailCandidateSelected.status,
          lia_insights: {},
          soft_skills: [],
          languages: {},
          certifications: []
        }) : null}
        onSuccess={() => {
          setShowSendEmailModal(false)
          setEmailCandidateSelected(null)
        }}
      />

      {/* Reveal Contact Modal */}
      {revealCandidate && (
        <RevealCreditsModal
          isOpen={showRevealModal}
          onClose={() => {
            setShowRevealModal(false)
            setRevealCandidate(null)
          }}
          // @ts-ignore TODO: fix type
          onConfirm={handleRevealContact}
          revealType={revealType}
          candidateName={revealCandidate.name}
          creditsRequired={revealType === 'email' ? 2 : 14}
        />
      )}

      {/* CV Preview Modal */}
      {parsedCVData && (
        <CVPreview
          isOpen={showCVPreviewModal}
          onClose={() => {
            setShowCVPreviewModal(false)
            setParsedCVData(null)
          }}
          parsedData={parsedCVData}
          onConfirm={handleCVConfirmed}
          jobVacancies={bulkJobVacancies.map(j => ({ id: j.id, title: j.title }))}
        />
      )}

      {/* Credit Confirmation Modal */}
      <CreditConfirmationModal
        open={showCreditConfirmation}
        onOpenChange={setShowCreditConfirmation}
        // @ts-ignore TODO: fix type
        creditEstimate={creditEstimate}
        // @ts-ignore TODO: fix type
        pearchSearchOptions={pearchSearchOptions}
        // @ts-ignore TODO: fix type
        onSearchOptionsChange={setPearchSearchOptions}
        onCancel={() => {
          setShowCreditConfirmation(false)
          setPendingSearchRequest(null)
        }}
        onConfirm={handleConfirmPearchSearch}
      />

      {/* Global Expansion Confirm Modal */}
      <GlobalExpansionConfirmModal
        open={showGlobalExpansionConfirm}
        onOpenChange={setShowGlobalExpansionConfirm}
        lastSuccessfulQuery={lastSuccessfulQuery}
        lastSearchQuery={lastSearchQuery}
        localResultsCount={localResultsCount}
        isExpandingToGlobal={isExpandingToGlobal}
        onConfirm={handleExpandToGlobal}
      />

      {/* Source Change Confirm Modal */}
      <SourceChangeConfirmModal
        open={showSourceChangeModal}
        onOpenChange={setShowSourceChangeModal}
        // @ts-ignore TODO: fix type
        pendingSourceChange={pendingSourceChange}
        onCancel={() => { setShowSourceChangeModal(false); setPendingSourceChange(null) }}
        onConfirm={confirmSourceChange}
      />

      {/* Contact Filter Confirm Modal */}
      <ContactFilterConfirmModal
        open={showContactFilterModal}
        onOpenChange={setShowContactFilterModal}
        // @ts-ignore TODO: fix type
        pendingContactFilter={pendingContactFilter}
        onCancel={() => { setShowContactFilterModal(false); setPendingContactFilter(null) }}
        onConfirm={confirmContactFilterChange}
      />

      {/* Save As Archetype Modal */}
      <SaveAsArchetypeModal
        open={showSaveAsArchetypeModal}
        onOpenChange={setShowSaveAsArchetypeModal}
        currentQuery={lastSuccessfulQuery || searchResults.query || ''}
        isCreatingArchetype={isCreatingArchetype}
        newArchetypeData={newArchetypeData}
        onClose={() => {
          if (isCreatingArchetype) {
            setIsCreatingArchetype(false)
            setArchetypeCreationStep('initial')
            setNewArchetypeData({})
          }
        }}
        onSave={(archetype, message) => {
          // @ts-ignore TODO: fix type
          setUserArchetypes(prev => [...prev, archetype])
          setShowSaveAsArchetypeModal(false)
          // @ts-ignore TODO: fix type
          setChatMessages(prev => [...prev, message])
          if (isCreatingArchetype) {
            setIsCreatingArchetype(false)
            setArchetypeCreationStep('initial')
            setNewArchetypeData({})
          }
        }}
      />

      {/* Advanced Filters Modal */}
      <AdvancedFiltersModal
        isOpen={showAdvancedSearch}
        onClose={() => setShowAdvancedSearch(false)}
        onApply={(filters) => {
          // @ts-ignore TODO: fix type
          setActiveSearchFilters(filters)
          setShowAdvancedSearch(false)
          const hideScope = (filters as Record<string, unknown>).general ? ((filters as Record<string, unknown>).general as Record<string, unknown>)?.hideViewedScope as string || "dont_hide" : "dont_hide"
          const hidePeriod = (filters as Record<string, unknown>).general ? ((filters as Record<string, unknown>).general as Record<string, unknown>)?.hideViewedPeriod as string || "all_time" : "all_time"
          hideViewedCandidates.setScope(hideScope)
          hideViewedCandidates.setPeriod(hidePeriod)
          if (hideScope !== "dont_hide") {
            hideViewedCandidates.fetchViewedCandidates()
          }
        }}
        initialFilters={activeSearchFilters}
        estimatedMatches={1000000}
      />

      {/* Add to List Modal */}
      <AddToListModal
        isOpen={showAddToListModal}
        onClose={() => {
          setShowAddToListModal(false)
          setAddToListCandidateIds([])
          setAddToListCandidateNames([])
        }}
        candidateIds={addToListCandidateIds}
        candidateNames={addToListCandidateNames}
        onSuccess={() => {
          toast({
            title: "Sucesso",
            description: "Candidatos adicionados à lista"
          })
        }}
      />

      {/* Share Search Modal */}
      <ShareSearchModal
        open={showShareSearchModal}
        onClose={() => {
          setShowShareSearchModal(false)
          setShareSearchCandidates([])
          setShareSearchTitle('')
        }}
        shareType="search"
        title={shareSearchTitle}
        candidateIds={shareSearchCandidates.map(c => c.id)}
        candidateCount={shareSearchCandidates.length}
        sourceQuery={lastSearchQuery || undefined}
      />

      {/* Add List to Vacancies Modal */}
      {selectedListForVacancies && (
        <AddListToVacanciesModal
          isOpen={showAddListToVacanciesModal}
          onClose={() => {
            setShowAddListToVacanciesModal(false)
            setSelectedListForVacancies(null)
          }}
          listId={selectedListForVacancies.id}
          listName={selectedListForVacancies.name}
          candidateCount={selectedListForVacancies.candidateCount}
          onSuccess={() => {
            toast({
              title: "Sucesso",
              description: "Candidatos adicionados às vagas selecionadas"
            })
          }}
        />
      )}

      {/* Add Candidates to Vacancy Modal */}
      <AddCandidatesToVacancyModal
        isOpen={showAddToVacancyModal}
        onClose={() => setShowAddToVacancyModal(false)}
        candidateIds={Array.from(selectedCandidatesForBatch)}
        candidateNames={candidates.filter(c => selectedCandidatesForBatch.has(c.id)).map(c => c.name)}
        currentRecruiterEmail={user?.email}
        onSuccess={() => {
          setSelectedCandidatesForBatch(new Set())
          toast({
            title: "Sucesso",
            description: "Candidatos adicionados à vaga"
          })
        }}
      />

      {/* Unsaved Pearch Warning Modal */}
      <UnsavedPearchWarningModal
        isOpen={showUnsavedWarningModal}
        onClose={() => {
          setShowUnsavedWarningModal(false)
          setPendingTabChange(null)
        }}
        onSaveAndExit={handleSaveAllAndExit}
        onExitWithoutSaving={handleExitWithoutSaving}
        unsavedCount={unsavedPearchCandidates.length}
        // @ts-ignore TODO: fix type
        unsavedCandidates={unsavedPearchCandidates}
        isSaving={isSavingToBase}
      />

      {/* Edit Query Modal */}
      <EditQueryModal
        isOpen={showEditQueryModal}
        onClose={() => setShowEditQueryModal(false)}
        initialValue={editQueryValue}
        activeFiltersCount={getActiveSearchFiltersCount()}
        searchSource={searchSource}
        onSearchSourceChange={setSearchSource}
        // @ts-ignore TODO: fix type
        pearchSearchOptions={pearchSearchOptions}
        // @ts-ignore TODO: fix type
        onPearchOptionsChange={setPearchSearchOptions}
        onOpenFilters={() => setShowAdvancedSearch(true)}
        onSubmitNatural={async (query, entities, mode, metadata) => {
          setSearchTerm(query)
          setLastSearchQuery(query)
          setLastSearchMode(mode || 'natural')
          // @ts-ignore TODO: fix type
          setLastSearchEntities(entities)
          // @ts-ignore TODO: fix type
          setLastSearchMetadata(metadata)
          await executeSearch(query, entities, mode || 'natural', metadata, false)
        }}
        onSubmitAI={async (query) => {
          setSearchTerm(query)
          setLastSearchQuery(query)
          setLastSearchMode('ai-natural')
          // @ts-ignore TODO: fix type
          setLastSearchEntities(null)
          await executeSearch(query, null, 'ai-natural', undefined, false)
        }}
      />

      {/* Preview Suggestion Modal */}
      <PreviewSuggestionModal
        // @ts-ignore TODO: fix type
        previewSuggestion={previewSuggestion}
        // @ts-ignore TODO: fix type
        previewingUserArchetype={previewingUserArchetype}
        onClose={() => {
          setPreviewSuggestion(null)
          setPreviewingUserArchetype(null)
        }}
        // @ts-ignore TODO: fix type
        buildFiltersFromTags={buildFiltersFromTags}
        onUpdateArchetype={(id, updates) => {
          // @ts-ignore TODO: fix type
          setUserArchetypes(prev => prev.map((a: unknown) =>
            (a as Record<string, unknown>).id === id ? { ...(a as object), ...updates } : a
          ))
        }}
        // @ts-ignore TODO: fix type
        onSaveArchetype={(newArchetype) => setUserArchetypes(prev => [...prev, newArchetype as Record<string, unknown>])}
        onExecuteSearch={async (query, filters, mode, metadata, usePearch) => {
          await executeSearch(query, filters as Record<string, unknown>, mode as string, metadata as Record<string, unknown>, usePearch)
        }}
        onSetLiaPromptValue={setLiaPromptValue}
        onSetActiveSearchTab={setActiveSearchTab}
      />

      {/* Delete Archetype Modal */}
      <DeleteArchetypeModal
        // @ts-ignore TODO: fix type
        archetypeToDelete={archetypeToDelete}
        onClose={() => setArchetypeToDelete(null)}
        onDeleted={(id) => setUserArchetypes(prev => prev.filter((a: unknown) => (a as Record<string, unknown>).id !== id))}
      />
    </>
  )
}
