"use client"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { List, Plus, Search, FolderOpen, Loader2 } from "lucide-react"
import { SharedSearchDetailsModal } from "@/components/modals/shared-search-details-modal"
import { AddToJobModal } from "@/components/modals/add-to-job-modal"
import { ShareSearchModal } from "@/components/modals/share-search-modal"
import { toast } from "sonner"

export type { SharedSearch } from "./lists-tab-types"
import { ListsTabProps } from "./lists-tab-types"
import { useListsTab } from "./use-lists-tab"
import { ListCard } from "./list-card"
import { SharedSearchesSection } from "./shared-searches-section"
import { ListFormModal, DeleteListDialog } from "./list-form-modal"

export function ListsTab({ onListSelect, onAddToJobs, onGoToSearch, onAddCandidateToList, onViewSharedDetails }: ListsTabProps) {
  const {
    lists,
    loading,
    searchTerm,
    setSearchTerm,
    showCreateModal,
    editingList,
    listToDelete,
    setListToDelete,
    formName,
    setFormName,
    formDescription,
    setFormDescription,
    formColor,
    setFormColor,
    saving,
    deleting,
    sharedSearches,
    loadingShared,
    showDetailsModal,
    setShowDetailsModal,
    selectedSharedSearch,
    showAddToJobModal,
    setShowAddToJobModal,
    selectedCandidateIds,
    selectedCandidateNames,
    feedbackComments,
    showShareModal,
    setShowShareModal,
    shareListData,
    setShareListData,
    filteredLists,
    totalCandidates,
    totalNewFeedbacks,
    openCreateModal,
    openEditModal,
    closeModal,
    handleSave,
    handleDelete,
    handleCopyLink,
    handleResendInvite,
    handleRevokeShare,
    handleViewDetails,
    handleCreateListFromShared,
    handleAddToJobFromShared,
    handleCreateJobFromShared,
    handleShareList,
    loadSharedSearches,
  } = useListsTab()

  const openAddCandidateModal = (list: { id: string; name: string }) => {
    if (onAddCandidateToList) {
      onAddCandidateToList(list.id, list.name)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-lg font-semibold text-lia-text-primary flex items-center gap-2">
            <List className="w-5 h-5 text-lia-text-secondary" />
            Listas de Candidatos
          </h2>
          <p className="text-xs text-lia-text-primary mt-0.5" aria-live="polite" aria-atomic="true">
            {lists.length} {lists.length === 1 ? 'lista' : 'listas'} • {totalCandidates} {totalCandidates === 1 ? 'candidato' : 'candidatos'} no total
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-lia-text-secondary" />
            <Input
              placeholder="Buscar listas..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-64 h-8 text-xs"
            />
          </div>

          <Button
            onClick={openCreateModal}
            size="sm"
            className="h-8 text-xs gap-1.5 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
          >
            <Plus className="w-3.5 h-3.5" />
            Nova Lista
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite" aria-label="Carregando...">
          <Loader2 className="w-6 h-6 animate-spin motion-reduce:animate-none text-lia-text-secondary" />
          <span className="ml-2 text-sm text-lia-text-primary">Carregando listas...</span>
        </div>
      ) : filteredLists.length > 0 ? (
        <div className="space-y-2">
          {filteredLists.map((list) => (
            <ListCard
              key={list.id}
              list={list}
              onSelect={onListSelect}
              onEdit={openEditModal}
              onDelete={setListToDelete}
              onAddToJobs={onAddToJobs}
              onAddCandidate={openAddCandidateModal}
              onShare={handleShareList}
            />
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-16 px-4">
          <div className="w-16 h-16 rounded-full flex items-center justify-center mb-4 bg-lia-bg-tertiary">
            <FolderOpen className="w-8 h-8 text-lia-text-tertiary" />
          </div>
          <h3 className="text-lg font-medium text-lia-text-primary mb-2">
            {searchTerm ? 'Nenhuma lista encontrada' : 'Nenhuma lista criada'}
          </h3>
          <p className="text-sm text-lia-text-primary text-center max-w-md mb-6" aria-live="polite" aria-atomic="true">
            {searchTerm
              ? `Não encontramos listas com o termo "${searchTerm}". Tente outro termo ou crie uma nova lista.`
              : 'Crie sua primeira lista para organizar candidatos de forma eficiente. Você pode agrupar candidatos por vaga, perfil ou qualquer critério.'}
          </p>
          {!searchTerm && (
            <Button
              onClick={openCreateModal}
              className="gap-2 bg-lia-btn-primary-bg hover:bg-lia-btn-primary-hover text-lia-btn-primary-text"
            >
              <Plus className="w-4 h-4" />
              Criar primeira lista
            </Button>
          )}
        </div>
      )}

      <SharedSearchesSection
        sharedSearches={sharedSearches}
        loadingShared={loadingShared}
        totalNewFeedbacks={totalNewFeedbacks}
        onViewDetails={handleViewDetails}
        onCopyLink={handleCopyLink}
        onResendInvite={handleResendInvite}
        onRevokeShare={handleRevokeShare}
      />

      <ListFormModal
        open={showCreateModal}
        editingList={editingList}
        formName={formName}
        formDescription={formDescription}
        formColor={formColor}
        saving={saving}
        onFormNameChange={setFormName}
        onFormDescriptionChange={setFormDescription}
        onFormColorChange={setFormColor}
        onSave={handleSave}
        onClose={closeModal}
      />

      <DeleteListDialog
        listToDelete={listToDelete}
        deleting={deleting}
        onDelete={handleDelete}
        onCancel={() => setListToDelete(null)}
      />

      <SharedSearchDetailsModal
        open={showDetailsModal}
        onClose={() => setShowDetailsModal(false)}
        sharedSearchId={selectedSharedSearch || ''}
        onCreateList={handleCreateListFromShared}
        onAddToJob={handleAddToJobFromShared}
        onCreateJob={handleCreateJobFromShared}
      />

      <AddToJobModal
        open={showAddToJobModal}
        onClose={() => setShowAddToJobModal(false)}
        candidateIds={selectedCandidateIds}
        candidateNames={selectedCandidateNames}
        feedbackComments={feedbackComments}
        sharedSearchId={selectedSharedSearch || undefined}
        onSuccess={() => {
          setShowAddToJobModal(false)
          loadSharedSearches()
          toast.success("Candidatos adicionados com sucesso!")
        }}
      />

      {shareListData && (
        <ShareSearchModal
          open={showShareModal}
          onClose={() => {
            setShowShareModal(false)
            setShareListData(null)
          }}
          shareType="list"
          title={shareListData.name}
          candidateIds={[]}
          candidateCount={shareListData.candidateCount}
          sourceListId={shareListData.id}
          onSuccess={() => {
            setShowShareModal(false)
            setShareListData(null)
            loadSharedSearches()
          }}
        />
      )}
    </div>
  )
}
